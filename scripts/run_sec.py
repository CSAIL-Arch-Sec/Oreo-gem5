from utils import *
from re_checkpoint import re_one_checkpoint
from pathlib import Path
import click
import multiprocessing


def get_double_page_fault_script():
    script = (f"/home/gem5/experiments/bin/double_page_fault\n"
              f"sleep 1\n"
              f"m5 exit")

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"double_page_fault.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def get_entrybleed_script():
    script = (f"/home/gem5/experiments/bin/entrybleed\n"
              f"sleep 1\n"
              f"m5 exit")

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"entrybleed.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def main():
    double_page_fault_path = get_double_page_fault_script()
    entrybleed_path = get_entrybleed_script()

    args_list = [
        # ["kvm", "o3", "0,0,0", "c,0,0", None, "2024-04-14-06-29-01", "", double_page_fault_path],
        # ["kvm", "o3", "1,1,1", "c,0,0", None, "2024-04-14-06-29-01", "", double_page_fault_path],
        ["kvm", "o3", "0,0,0", "c,0,0", None, "2024-04-14-06-29-01", "", entrybleed_path],
        ["kvm", "o3", "1,1,1", "c,0,0", None, "2024-04-14-06-29-01", "", entrybleed_path],
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
