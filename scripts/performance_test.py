import click
import multiprocessing
import numpy as np
import re
import subprocess
from pathlib import Path
import random
from utils import *


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent
exp_dir = proj_dir.parent / "experiments"


def get_script_name(suffix):
    return f"performance_test_{suffix}"


def gen_random_performance_script(after_boot_script_dir: Path, random_id: int, bench_order: list):
    # bench_list = list(range(len(performance_test_list)))
    # random.shuffle(bench_list)
    run_cmd_list = list(map(lambda x: f"./bin/LEBench-hook {x} 1\n", bench_order))
    run_cmd = "".join(run_cmd_list)

    s = f"cd /home/gem5/LEBench-Sim\n" \
        f"rm -f lebench_stats.csv\n" \
        f"{run_cmd}" \
        f"m5 writefile lebench_stats.csv\n" \
        f"echo 'writing lebench_stats.csv back to host :D'\n" \
        f"sleep 1\n" \
        f"m5 exit\n"

    output_path = after_boot_script_dir / get_script_name(f"random_{random_id}")
    with output_path.open(mode="w") as output_file:
        output_file.write(s)

    return output_path


def gen_performance_script(bench_id: int, after_boot_script_dir: Path):
    s = f"cd /home/gem5/LEBench-Sim\n" \
        f"rm -f lebench_stats.csv\n" \
        f"./bin/LEBench-hook {bench_id} 1\n" \
        f"m5 writefile lebench_stats.csv\n" \
        f"echo 'writing lebench_stats.csv back to host :D'\n" \
        f"sleep 1\n" \
        f"m5 exit\n"

    output_path = after_boot_script_dir / get_script_name(bench_id)
    with output_path.open(mode="w") as output_file:
        output_file.write(s)

    return output_path


def run_performance_one(
        bench_id: int,
        protect_text: bool,
        protect_module: bool,
        protect_user: bool,
        checkpoint_dir: Path,
        after_boot_script_dir: Path,
        output_dir: Path,
        gem5_kaslr_delta: int = 0,
        gem5_module_kaslr_delta: int = 12,
        gem5_user_aslr_delta: int = 0,
        image_suffix: str = "",
        bench_order = None,
):
    # load_addr_offset = ~np.uint64(kaslr_offset) + np.uint64(1) + np.uint64(0x1000000)

    perf_script_path = gen_performance_script(bench_id, after_boot_script_dir)
    # NOTE: The bench_id here refers to the number of random runs.
    # perf_script_path = gen_random_performance_script(after_boot_script_dir, bench_id, bench_order)

    # gem5_str = "./build/X86_MOESI_hammer/gem5.fast"
    gem5_str = "./build/X86/gem5.fast"
    gem5_script = "configs/example/gem5_library/gem5-configs/x86-restore.py"

    output_log = output_dir / "output.log"

    cmd = [
        "M5_OVERRIDE_PY_SOURCE=true",
        gem5_str,
        # debug_option,
        # debug_start,
        # f"--debug-file={output_dir}/{trace_name}.out.gz",
        f"--outdir={output_dir}",
        gem5_script,
        f"--gem5-kaslr-delta={gem5_kaslr_delta}",
        f"--gem5-module-kaslr-delta={gem5_module_kaslr_delta}",
        f"--gem5-user-aslr-delta={gem5_user_aslr_delta}",
        # f"--load-addr-offset={load_addr_offset}",
        f"--script={perf_script_path}",
        "--cpu-type=O3",
        "--redirect-stderr",
        f"--stderr-file={output_log}",
        "--redirect-stdout",
        f"--stdout-file={output_log}",
        f"--checkpoint-dir={checkpoint_dir}",
        f"--outputs-dir={output_dir}"
    ]

    if protect_text:
        cmd.append("--protect-kaslr")

    if protect_module:
        cmd.append("--protect-module-kaslr")

    if protect_user:
        cmd.append("--protect-user-aslr")

    if image_suffix:
        cmd.append(f"--image-suffix={image_suffix}")

    cmd_str = " ".join(cmd)
    print(cmd_str)
    with output_log.open(mode="w") as output_file:
        p = subprocess.run(
            cmd_str,
            shell=True,
            cwd=str(proj_dir),
            stdout=output_file,
            stderr=output_file,
        )

    if p.returncode:
        print(f"!!! Run {bench_id} fails")
    else:
        print(f"!!! Run {bench_id} success")


def test_one_setup(
        bench_id: int,
        protect_text: bool,
        protect_module: bool,
        protect_user: bool,
        checkpoint_dir_suffix: str,
        after_boot_script_dir: Path,
        bench_order: list
):
    mode_name = get_mode_name(protect_text, protect_module, protect_user)

    checkpoint_dir = proj_dir / "result" / f"{mode_name}_checkpoint{checkpoint_dir_suffix}" / "default-save" / "m5out-gen-cpt"
    output_dir = proj_dir / "result" / f"{mode_name}_lebench_new_{bench_id}"
    # trace_name = f"trace_{mode_name}_{re.sub(r',', r'_', debug_flags)}_{test_offset}"

    output_dir.mkdir(exist_ok=True)

    run_performance_one(
        bench_id=bench_id,
        protect_text=protect_text,
        protect_module=protect_module,
        protect_user=protect_user,
        checkpoint_dir=checkpoint_dir,
        after_boot_script_dir=after_boot_script_dir,
        output_dir=output_dir,
        image_suffix="",
        bench_order=bench_order,
    )


@click.command()
@click.option(
    "--run-list",
    type=click.STRING,
    default=""
)
@click.option(
    "--check-suffix",
    type=click.STRING,
    default="_0"
)
def main(run_list: str, check_suffix: str):
    after_boot_script_dir = script_dir / "after_boot"
    after_boot_script_dir.mkdir(exist_ok=True)

    arg_list = []

    protection_list = [
        [False, False, False],
        [False, True, False],
        # [True, False, False],
        # [True, True, False],
    ]

    if run_list == "":
        # bench_list = list(range(len(performance_test_list)))
        # NOTE: We run the random test 30 times.
        idx_list = list(range(len(performance_test_list)))
    else:
        idx_list = list(map(lambda x: int(x), run_list.split(",")))

    # for i in [13, 22, 16]:
    print(idx_list)
    for i in idx_list:
        bench_list = list(range(len(performance_test_list)))
        random.shuffle(bench_list)
        print(bench_list)
        for protect_text, protect_module, protect_user in protection_list:
            arg_list.append([i, protect_text, protect_module, protect_user, check_suffix, after_boot_script_dir, bench_list])
        # break

    print(arg_list)

    with multiprocessing.Pool(80) as p:
        p.starmap(test_one_setup, arg_list)


if __name__ == '__main__':
    main()

