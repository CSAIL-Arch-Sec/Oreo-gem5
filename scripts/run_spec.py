import re
import subprocess

from utils import *
from gen_checkpoint import gen_one_checkpoint
from re_checkpoint import re_one_checkpoint
from pathlib import Path
import click
import multiprocessing


def gen_cpt_for_sim_setup(sim_setup_list: list, use_uuid: bool):
    def get_gen_setup(
            sim_option: str, debug_flags: str,
            starting_core: str, swith_core: str,
            protect_args: str,
            delta_args: str,
            cpt_tick: int,
            uuid_str: str,
            suffix: str,
    ):
        if cpt_tick is None:
            cpt_str = ""
        else:
            cpt_str = str(cpt_tick)
        return [starting_core, 1, protect_args, delta_args, cpt_str, use_uuid, suffix]

    gen_setup_list = list(map(lambda x: get_gen_setup(*x), sim_setup_list))
    print(gen_setup_list)

    with multiprocessing.Pool(1) as p:
        pool_ret = p.starmap(gen_one_checkpoint, gen_setup_list)

    assert len(pool_ret) == len(sim_setup_list)

    # TODO: Test cpt related arg generation!!!
    for i in range(len(pool_ret)):
        output_dir = pool_ret[i]
        if not output_dir:
            return -1
        dir_name = output_dir.name
        if dir_name != "default":
            sim_setup_list[i][7] = dir_name # NOTE!!! Hard code order of parameter here!!!

    print(pool_ret)

    return 0


def copy_all_spec_cmd(
        server_ip: str,
        output_base_dir: Path,
        bench_list: list,
):
    input_base_dir = Path("/home/gem5/spec2017/benchspec/CPU")

    for bench_name in bench_list:
        run_dir = Path(f"{bench_name}/run/run_base_refrate_mytest-m64.0000")
        input_dir = input_base_dir / run_dir
        input_path = input_dir / "speccmds.cmd"
        output_dir = output_base_dir / bench_name
        output_dir.mkdir(exist_ok=True, parents=True)
        scp_cmd = f"scp {server_ip}:{input_path} {output_dir}"
        subprocess.run(scp_cmd, shell=True)
        cwd_path = output_dir / "cwd"
        with cwd_path.open(mode="w") as cwd_file:
            cwd_file.write(f"{input_dir}\n")


def convert_all_spec_cmd(all_cmd_dir: Path, bench_list: list):
    for bench_name in bench_list:
        cmd_dir = all_cmd_dir / bench_name
        input_path = cmd_dir / "speccmds.cmd"
        output_path = cmd_dir / "mycmds.cmd"

        with input_path.open() as input_file:
            lines = input_file.readlines()

        result = []
        for line in lines:
            x = re.search(r"^-o \S+ -e \S+ ([^>]+) > \S+ 2>> \S+$", line)
            if x is not None:
                result.append(f"{x.group(1)}\n")

        with output_path.open(mode="w") as output_file:
            output_file.writelines(result)


def gen_spec_script_scheduled(
        cwd: str, cmd: str,
        output_path: Path,
        user_delta: int,
        warmup_ns: int = 10 ** 9,
        sim_ns: int = 10 ** 9,
):
    reset_wait_ns = 1000000
    exit_wait_ns = 10000000

    s = (
        f"cd /home/gem5/experiments/modules\n"
        f"insmod set_protection.ko user_delta={user_delta}\n"
        f"cd {cwd}\n"
        f"m5 exit {warmup_ns + sim_ns + exit_wait_ns} &\n"
        f"m5 resetstats {reset_wait_ns} &\n"
        f"m5 dumpresetstats {warmup_ns + reset_wait_ns} &\n"
        f"m5 dumpstats {warmup_ns + sim_ns + reset_wait_ns} &\n"
        f"{cmd}\n"
        f"echo 'finish runspec with ret code $?'\n"
        f"sleep 1\n"
        f"m5 exit\n"
    )

    with output_path.open(mode="w") as output_file:
        output_file.write(s)


def gen_spec_script_path_list(
        bench_name_list: list, bench_input_id_list: list,
        output_dir: Path,
        user_delta: int,
        warmup_ns: int = 10 ** 9,
        sim_ns: int = 10 ** 9,
):
    output_dir.mkdir(exist_ok=True)
    all_cmd_dir = script_dir / "spec_cmd"
    result = []
    for k, bench_name in enumerate(bench_name_list):
        cmd_dir = all_cmd_dir / bench_name
        with (cmd_dir / "cwd").open() as cwd_file:
            cwd_str = cwd_file.read().strip()
        with (cmd_dir / "mycmds.cmd").open() as cmd_file:
            cmd_list = cmd_file.readlines()

        for i, cmd_str in enumerate(cmd_list):
            output_path = output_dir / f"{bench_name}-input{i}-delta{user_delta}.rcS"
            gen_spec_script_scheduled(
                cwd=cwd_str,
                cmd=cmd_str,
                user_delta=user_delta,
                output_path=output_path,
                warmup_ns=warmup_ns, sim_ns=sim_ns
            )
            input_id_list = bench_input_id_list[k]
            if input_id_list is None or (i in input_id_list):
                result.append(output_path)
    return result


def gen_spec2017_script_full(
        bench_name: str, size: str,
        output_dir: Path,
):
    s = (
        f"cd /home/gem5/spec2017\n"
        f"source shrc\n"
        f"m5 resetstats\n"
        f"runcpu --size {size} --iterations 1 --config myconfig.x86.cfg --define gcc_dir=\"/usr\" --noreportable --nobuild {bench_name}\n"
        # f"echo 'finish runspec with ret code $?'\n"
        f"m5 dumpresetstats\n"
        f"m5 exit\n"
    )

    output_path = output_dir / f"{bench_name}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(s)

    return output_path


def gen_spec2017_script_path_list(
        bench_name_list: list, size: str,
        gen_fun
):
    output_dir = script_dir / "spec2017_scripts"
    output_dir.mkdir(exist_ok=True)
    return list(map(lambda x: gen_fun(x, size, output_dir), bench_name_list))


def gen_spec2006_script_single_bench(
        bench_name: str, size: str, output_dir: Path,
        warmup_ns: int = 10 ** 9,
        sim_ns: int = 10 ** 9,
):
    # warmup_ns = 10 ** 10
    # warmup_ns = 10 ** 9
    # sim_ns = 10 ** 9

    reset_wait_ns = 1000000
    exit_wait_ns = 5000000

    s = (
        f"cd /home/gem5/spec2006\n"
        f"source shrc\n"
        f"ls\n"
        # f"m5 resetstats\n"
        # f"m5 dumpstats\n"
        f"m5 exit {warmup_ns + sim_ns + exit_wait_ns} &\n"
        f"m5 resetstats {reset_wait_ns} &\n"
        f"m5 dumpresetstats {warmup_ns + reset_wait_ns} &\n"
        f"m5 dumpstats {warmup_ns + sim_ns + reset_wait_ns} &\n"
        # f"echo hh\n"
        # f"sleep 1\n"
        f"runspec --size {size} --iterations 1 --config myconfig.cfg --noreportable --nobuild {bench_name}\n"
        f"echo 'finish runspec with ret code $?'\n"
        # f"m5 exit\n"
    )

    output_path = output_dir / f"{bench_name}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(s)

    return output_path


def gen_spec2006_script_path_list(
        bench_name_list: list, size: str,
        warmup_ns: int = 10 ** 9,
        sim_ns: int = 10 ** 9,
):
    output_dir = script_dir / "spec_scripts"
    output_dir.mkdir(exist_ok=True)
    return list(map(lambda x: gen_spec2006_script_single_bench(x, size, output_dir, warmup_ns=warmup_ns, sim_ns=sim_ns), bench_name_list))


def gen_full_arg_list(sim_arg_list: list, exp_script_path_list: list):
    result = []
    for a in sim_arg_list:
        for b in exp_script_path_list:
            new_args = a + [b]
            result.append(new_args)
    return result


@click.command()
@click.option(
    "--copy-spec-cmd",
    is_flag=True,
)
@click.option(
    "--convert-spec-cmd",
    is_flag=True,
)
@click.option(
    "--gen-cpt",
    is_flag=True,
)
@click.option(
    "--use-uuid",
    is_flag=True,
)
@click.option(
    "--begin-cpt",
    type=click.INT,
)
@click.option(
    "--num-cpt",
    type=click.INT,
)
@click.option(
    "--num-cores",
    type=click.INT,
    default=12,
)
@click.option(
    "--spec-size",
    type=click.STRING,
    default="ref"
)
@click.option(
    "--user-delta",
    type=click.INT,
    default=32,
)
@click.option(
    "--warmup-ns",
    type=click.INT,
    default=1000000000
)
@click.option(
    "--sim-ns",
    type=click.INT,
    default=1000000000
)
def main(
        copy_spec_cmd: bool,
        convert_spec_cmd: bool,
        gen_cpt: bool,
        use_uuid: bool,
        begin_cpt: int,
        num_cpt: int,
        num_cores: int,
        spec_size: str,
        user_delta: int,
        warmup_ns: int,
        sim_ns: int,
):
    if copy_spec_cmd:
        copy_all_spec_cmd(
            "gem5@172.16.65.128",
            script_dir / "spec_cmd",
            spec2017_intrate_bench_list
        )

    if convert_spec_cmd:
        convert_all_spec_cmd(
            script_dir / "spec_cmd",
            spec2017_intrate_bench_list
        )

    if copy_spec_cmd or convert_spec_cmd:
        return

    sim_setup_base = [
        ["fast", "", "kvm", "o3", "0,0,0", "c,c,0", None, ""],
        ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, ""],
        # ["fast", "", "kvm", "o3", "1,1,1", "c,c,1", None, ""],
    ]

    sim_setup = []

    for base_setup in sim_setup_base:
        for i in range(begin_cpt, begin_cpt + num_cpt):
            sim_setup.append(base_setup + [str(i)])

    print(sim_setup)

    # run_bench_list = [ "401.bzip2" ]
    # run_bench_list = spec2006_bench_list
    # run_bench_list = [ "525.x264_r" ]

    # run_bench_list = [ "557.xz_r" ]
    # bench_input_id_list = [[2]]

    run_bench_list = spec2017_intrate_bench_list
    bench_input_id_list = [ None ] * len(run_bench_list)

    # exp_script_path_list = gen_spec2006_script_path_list(run_bench_list, spec_size, warmup_ns=warmup_ns, sim_ns=sim_ns)
    # exp_script_path_list = gen_spec2017_script_path_list(run_bench_list, spec_size, gen_spec2017_script_full)
    exp_script_path_list = gen_spec_script_path_list(
        bench_name_list=run_bench_list, bench_input_id_list=bench_input_id_list,
        user_delta=user_delta,
        output_dir=script_dir / "spec2017_scripts", warmup_ns=warmup_ns, sim_ns=sim_ns
    )
    for x in exp_script_path_list:
        print(x)

    if gen_cpt:
        # NOTE: This would change sim_setup!!!
        ret = gen_cpt_for_sim_setup(sim_setup_list=sim_setup, use_uuid=use_uuid)
        if ret:
            print("Error when generating checkpoint. Stopping...")
            return
    else:
        for s in sim_setup:
            s[7] = "default_" + s[8]

    args_list = gen_full_arg_list(sim_setup, exp_script_path_list)
    for x in args_list:
        print(x)

    with multiprocessing.Pool(num_cores) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
