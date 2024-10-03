from utils import *
from re_checkpoint import re_one_checkpoint
from pathlib import Path
import click
import multiprocessing


def get_entrybleed_script():
    script = (
        f"cd /home/gem5/experiments/modules\n"
        f"insmod set_protection.ko user_delta=32\n"
        f"/home/gem5/experiments/bin/entrybleed\n"
        f"sleep 1\n"
        f"m5 exit"
    )

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"entrybleed.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def get_blindside_script(probe_module: int, delta: int):
    script = (
        f"cd /home/gem5/experiments/modules\n"
        f"insmod set_protection.ko user_delta=32\n"
        f"cd /home/gem5/experiments/modules\n"
        f"insmod blindside_kernel.ko\n"
        f"/home/gem5/experiments/bin/blindside {probe_module} {delta:03}\n"
        # f"sleep 1\n"
        # f"echo {delta:03}\n"
        f"m5 exit"
    )

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"blindside_{probe_module}_{delta:02x}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def main():
    entrybleed_path = get_entrybleed_script()

    blindside_path_0c = get_blindside_script(1, 0xc)
    blindside_path_0d = get_blindside_script(1, 0xd)

    # The following list specifies arguments passed to re_one_checkpoint
    #   for running all security evaluation tasks
    args_list = [
        # Prefetch attack
        # Run baseline
        ["fast", "", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", entrybleed_path],
        # Run Oreo
        ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", entrybleed_path],

        # Leakage path 1 and 2
        # Run baseline (and probe a valid address speculatively)
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_0c, True],
        # Run baseline (and probe an invalid address speculatively)
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_0d, True],
        # Run Oreo (and probe a valid address speculatively)
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_0c, True],
        # Run Oreo (and probe an invalid address speculatively)
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_0d, True],
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
