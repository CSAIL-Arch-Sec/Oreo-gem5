from utils import *
from gen_checkpoint import gen_one_checkpoint
from re_checkpoint import re_one_checkpoint
from pathlib import Path
import click
import multiprocessing


def gen_cpt_for_sim_setup(sim_setup_list: list, use_uuid: bool):
    def get_gen_setup(
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
        return [starting_core, protect_args, delta_args, cpt_str, use_uuid, suffix]

    gen_setup_list = list(map(lambda x: get_gen_setup(*x), sim_setup_list))
    print(gen_setup_list)

    with multiprocessing.Pool(16) as p:
        pool_ret = p.starmap(gen_one_checkpoint, gen_setup_list)

    assert len(pool_ret) == len(sim_setup_list)

    # TODO: Test cpt related arg generation!!!
    for i in range(len(pool_ret)):
        output_dir = pool_ret[i]
        if not output_dir:
            return -1
        dir_name = output_dir.name
        if dir_name != "default":
            sim_setup_list[i][5] = dir_name # NOTE!!! Hard code order of parameter here!!!

    print(pool_ret)

    return 0


def gen_lebench_script_single_bench(bench_id: int, output_dir: Path):
    s = f"cd /home/gem5/LEBench-Sim\n" \
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
    "--gen-cpt",
    is_flag=True,
)
@click.option(
    "--use-uuid",
    is_flag=True,
)
def main(gen_cpt: bool, use_uuid: bool):
    sim_setup = [
        ["kvm", "o3", "0,0,0", "0,0,0", None, "", ""],
        ["kvm", "o3", "0,0,0", "c,0,0", None, "", ""],
        # ["kvm", "o3", "1,0,0", "c,0,0", None, "", ""],
        ["kvm", "o3", "1,1,0", "c,0,0", None, "", ""],
    ]

    lebench_id_list = list(range(len(performance_test_list)))
    rerun_list = ["context-switch", "thrcreate", "big-select"]

    exp_script_path_list = gen_lebench_script_path_list(lebench_id_list)
    for x in exp_script_path_list:
        print(x)

    if gen_cpt:
        # NOTE: This would change sim_setup!!!
        ret = gen_cpt_for_sim_setup(sim_setup_list=sim_setup, use_uuid=use_uuid)
        if ret:
            print("Error when generating checkpoint. Stopping...")
            return

    args_list = gen_full_arg_list(sim_setup, exp_script_path_list)
    for x in args_list:
        print(x)

    with multiprocessing.Pool(16) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
