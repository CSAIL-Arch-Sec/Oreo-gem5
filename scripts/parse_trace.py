import re
import gzip
from utils import *
from pathlib import Path


def grep_file(input_path: Path, output_dir: Path, match_list: list):
    output_dict = {}
    for _, name, _ in match_list:
        output_dict[name] = []

    with gzip.open(input_path, mode="rb") as input_file:
        s = input_file.read()
        lines = s.decode().split("\n")
        print(len(lines))

    # with input_path.open(mode="r") as input_file:
    #     lines = input_file.readlines()

    for line in lines:
        # used = False
        for pattern, name, extract_func in match_list:
            if pattern in line:
                x = extract_func(line)
                output_dict[name].append(x)
                # used = True
        # if not used:
        #     print(line)

    output_dir.mkdir(exist_ok=True, parents=True)

    for name, output_lines in output_dict.items():
        output_path = output_dir / name
        with output_path.open(mode="w") as output_file:
            output_file.writelines(output_lines)


def extract_branch_pred(line: str):
    # x = re.search(r"\(([a-z\d]+)=>[a-z\d]+\)", line)
    x = re.search(r"PC:(0x[a-z\d]+)", line)
    assert x is not None
    return x.group(1) + "\n"


def extract_tlb(line: str):
    return line.strip().split()[-1][:-1] + "\n"


def extract_walker(line: str):
    x = re.search(r"Make request for vaddr ([a-z\d]+), paddr ([a-z\d]+)", line)
    if x:
        return f"{x.group(1)}\n{x.group(2)}\n"
    x = re.search(r"New step paddr ([a-z\d]+)", line)
    if x is not None:
        return f"{x.group(1)}\n"
    return ""


def extract_cache(line: str):
    if "found" in line:
        return line.strip().split()[-2] + "\n"
    return line.strip().split()[-1] + "\n"


def extract_dram(line: str):
    x = re.search(r"Address: ([a-z\d]+) Rank", line)
    assert x is not None
    return x.group(1) + "\n"


def main():
    match_list = [
        ["Branch predictor predicted", "branchPred", extract_branch_pred],
        ["tb: Translating vaddr", "tlb", extract_tlb],
        ["itb: Translating vaddr", "iTLB", extract_tlb],
        ["dtb: Translating vaddr", "dTLB", extract_tlb],
        ["itb.walker: @@@", "iTLBWalker", extract_walker],
        ["dtb.walker: @@@", "dTLBWalker", extract_walker],
        ["cache:", "cache", extract_cache],
        ["board.cache_hierarchy.ruby_system.l1_controllers.L1Icache:", "L1ICache", extract_cache],
        ["board.cache_hierarchy.ruby_system.l1_controllers.L1Dcache:", "L1DCache", extract_cache],
        ["board.cache_hierarchy.ruby_system.l2_controllers.L2cache", "L2Cache", extract_cache],
        ["dram: Address:", "DRAM", extract_dram],
    ]

    path_0_c = proj_dir / "result/restore_ko_000_0c0c00/blindside_1_0c_/trace.out.gz"
    path_0_d = proj_dir / "result/restore_ko_000_0c0c00/blindside_1_0d_/trace.out.gz"
    path_1_c = proj_dir / "result/restore_ko_111_0c0c00/blindside_1_0c_/trace.out.gz"
    path_1_d = proj_dir / "result/restore_ko_111_0c0c00/blindside_1_0d_/trace.out.gz"

    output_dir = script_dir / "plot"

    grep_file(path_0_c, output_dir / "000_0c_2", match_list)
    grep_file(path_0_d, output_dir / "000_0d_2", match_list)
    grep_file(path_1_c, output_dir / "111_0c_2", match_list)
    grep_file(path_1_d, output_dir / "111_0d_2", match_list)


if __name__ == '__main__':
    main()
