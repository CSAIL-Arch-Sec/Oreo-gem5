import click
import multiprocessing
import numpy as np
import re
import subprocess
from pathlib import Path
from utils import *


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent
exp_dir = proj_dir.parent / "experiments"


def get_script_name(suffix):
    return f"performance_test_{suffix}"


def gen_performance_script(bench_id: int, after_boot_script_dir: Path):
    s = f"cd /home/gem5/LEBench-Sim\n" \
        f"rm -f lebench_stats.csv\n" \
        f"./bin/LEBench-run {bench_id} 1\n" \
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
        checkpoint_dir: Path,
        after_boot_script_dir: Path,
        output_dir: Path,
        kaslr_offset: int = 0xc000000,
        image_suffix: str = "",
):
    load_addr_offset = ~np.uint64(kaslr_offset) + np.uint64(1) + np.uint64(0x1000000)

    perf_script_path = gen_performance_script(bench_id, after_boot_script_dir)

    gem5_str = "./build/X86/gem5.opt"
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
        f"--kaslr-offset={kaslr_offset}",
        f"--load-addr-offset={load_addr_offset}",
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
        print(f"!!! Run {bench_id} {performance_test_list[bench_id]} fails")
    else:
        print(f"!!! Run {bench_id} {performance_test_list[bench_id]} success")


def test_one_setup(
        bench_id: int,
        protect_text: bool,
        protect_module: bool,
        checkpoint_dir_suffix: str,
        after_boot_script_dir: Path,
):
    mode_name = get_mode_name(protect_text, protect_module)

    checkpoint_dir = proj_dir / "result" / f"{mode_name}_checkpoint{checkpoint_dir_suffix}" / "default-save" / "m5out-gen-cpt"
    output_dir = proj_dir / "result" / f"{mode_name}_lebench_{bench_id}"
    # trace_name = f"trace_{mode_name}_{re.sub(r',', r'_', debug_flags)}_{test_offset}"

    output_dir.mkdir(exist_ok=True)

    run_performance_one(
        bench_id=bench_id,
        protect_text=protect_text,
        protect_module=protect_module,
        checkpoint_dir=checkpoint_dir,
        after_boot_script_dir=after_boot_script_dir,
        output_dir=output_dir,
        kaslr_offset=0xc000000,
        image_suffix="",
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
        [False, False],
        [False, True],
        [True, False],
        [True, True],
    ]

    if run_list == "":
        bench_list = list(range(len(performance_test_list)))
    else:
        bench_list = list(map(lambda x: int(x), run_list.split(",")))

    # for i in [13, 22, 16]:
    for i in bench_list:
        for protect_text, protect_module in protection_list:
            arg_list.append([i, protect_text, protect_module, check_suffix, after_boot_script_dir])
        # break

    print(arg_list)

    with multiprocessing.Pool(80) as p:
        p.starmap(test_one_setup, arg_list)


if __name__ == '__main__':
    main()

