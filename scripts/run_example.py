from utils import *
from re_checkpoint import re_one_checkpoint
from pathlib import Path
import click
import multiprocessing


def get_hello_script():
    script = (
        f"cd /home/gem5/experiments/modules\n"
        f"insmod set_protection.ko user_delta=32\n"
        f"/home/gem5/experiments/bin/hello\n"
        f"sleep 1\n"
        f"m5 exit"
    )

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"hello.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def get_hello_invalid_script():
    script = (
        f"cd /home/gem5/experiments/modules\n"
        f"insmod set_protection.ko user_delta=32\n"
        f"/home/gem5/experiments/bin/hello_invalid\n"
        f"sleep 1\n"
        f"m5 exit"
    )

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"hello_invalid.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def main():
    hello_path = get_hello_script()
    hello_invalid_path = get_hello_invalid_script()
    args_list = [
        # Run an example program that prints user function pointer with non-canonical bits randomized
        # Check result/restore_ko_111_0c0c00/hello_/board.pc.com_1.device to check the example program's output
        ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", hello_path],
        # Run an example program that non-speculatively accesses an address with incorrect ASLR offset
        # gem5 will simply raise an exception
        # Check result/restore_ko_111_0c0c00/hello_invalid_/board.pc.com_1.device to check the example program's output
        # Check result/restore_ko_111_0c0c00/hello_invalid_/stderr.log to check the exception output
        ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", hello_invalid_path],
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
