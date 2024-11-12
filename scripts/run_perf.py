from utils import *
from gen_checkpoint import gen_one_checkpoint
from re_checkpoint import re_one_checkpoint
from pathlib import Path
import click
import multiprocessing


def gen_cpt_for_sim_setup(sim_setup_list: list, use_uuid: bool, disk_root_partition: str):
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
        return [starting_core, 2, protect_args, delta_args, cpt_str, use_uuid, suffix, disk_root_partition]

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


def gen_lebench_script_single_bench(bench_id: int, output_dir: Path):
    s = f"cd /home/gem5/experiments/modules\n"\
        f"insmod set_protection.ko user_delta=32\n"\
        f"cd /home/gem5/LEBench-Sim\n" \
        f"rm -f lebench_stats.csv\n" \
        f"./bin/LEBench-hook {bench_id} 1\n" \
        f"m5 writefile {lebench_result_name}\n" \
        f"echo 'writing {lebench_result_name} back to host :D'\n" \
        f"sleep 1\n" \
        f"m5 exit\n"

    output_path = output_dir / f"{get_lebench_script_name(bench_id)}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(s)

    return output_path


def gen_lebench_script_path_list(bench_id_list: list):
    output_dir = script_dir / "lebench_scripts"
    output_dir.mkdir(exist_ok=True)
    return list(map(lambda x: gen_lebench_script_single_bench(x, output_dir), bench_id_list))


def gen_full_arg_list(sim_arg_list: list, exp_script_path_list: list):
    result = []
    for a in sim_arg_list:
        for b in exp_script_path_list:
            new_args = a + [b]
            result.append(new_args)
    return result


@click.command()
@click.option(
    "--disk-root-partition",
    type=click.STRING,
    default="1",
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
def main(disk_root_partition: str, gen_cpt: bool, use_uuid: bool, begin_cpt: int, num_cpt: int, num_cores: int):
    sim_setup_base = [
        # ["fast", "", "kvm", "o3", "0,0,0", "0,0,0", None, ""],
        ["fast", "", "kvm", "o3", "0,0,0", "c,c,0", None, ""],
        # ["fast", "", "kvm", "o3", "1,0,0", "c,c,0", None, ""],
        # ["fast", "", "kvm", "o3", "1,1,0", "c,c,0", None, ""],
        ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, ""],
    ]

    sim_setup = []

    for base_setup in sim_setup_base:
        for i in range(begin_cpt, begin_cpt + num_cpt):
            sim_setup.append(base_setup + [str(i)])

    print(sim_setup)

    lebench_id_list = list(range(len(performance_test_list)))
    # lebench_id_list = [0, 11, 22]
    # lebench_id_list = [0]
    rerun_list = ["context-switch", "thrcreate", "big-select"]

    exp_script_path_list = gen_lebench_script_path_list(lebench_id_list)
    for x in exp_script_path_list:
        print(x)

    if gen_cpt:
        # NOTE: This would change sim_setup!!!
        ret = gen_cpt_for_sim_setup(sim_setup_list=sim_setup, use_uuid=use_uuid, disk_root_partition=disk_root_partition)
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
