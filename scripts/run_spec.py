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
        return [starting_core, 2, protect_args, delta_args, cpt_str, use_uuid, suffix]

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
        gen_cpt: bool,
        use_uuid: bool,
        begin_cpt: int,
        num_cpt: int,
        num_cores: int,
        spec_size: str,
        warmup_ns: int,
        sim_ns: int,
):
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
    run_bench_list = spec2017_intrate_bench_list

    # exp_script_path_list = gen_spec2006_script_path_list(run_bench_list, spec_size, warmup_ns=warmup_ns, sim_ns=sim_ns)
    exp_script_path_list = gen_spec2017_script_path_list(run_bench_list, spec_size, gen_spec2017_script_full)
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
