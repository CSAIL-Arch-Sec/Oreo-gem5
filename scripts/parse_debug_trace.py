import gzip
import re
from pathlib import Path


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent


def read_file(input_path: Path):
    i = 0
    with gzip.open(input_path, "r") as input_file:
        for line in input_file:
            if i % 10000000 == 0:
                print("i =", i)
            i += 1
    print(i)


def mask_delta(line: str):
    return re.sub(
        r"(.\(``[\d|a-z]*''=>``[\d|a-z]*''\))",
        "",
        line
    )



def comp_lines(line1: str, line2: str):
    return mask_delta(line1) == mask_delta(line2)


def comp_two_traces(input_path1: Path, input_path2: Path):
    with gzip.open(input_path1, "r") as input_file1, gzip.open(input_path2, "r") as input_file2:
        i = 0
        j = 0
        while True:
            i += 1
            if i % 10000000 == 0:
                print("i =", i)
            line1 = input_file1.readline()
            line2 = input_file2.readline()
            if line1 is not None and line2 is not None:
                if not comp_lines(str(line1), str(line2)):
                    print(f"Diff at line {i}: {line1} != {line2}")
                    j += 1
                    if j > 100:
                        return False
            elif line1 is None and line2 is None:
                print("Same trace, end comparison")
                return True
            else:
                print(f"Diff at line {i}: {input_path1} and {input_path2} have different length")
                return False


def main():
    # comp_two_traces(
    #     proj_dir / "result/protect_both_restore_0/trace_protect_both_Fetch_Commit_0.out.gz",
    #     proj_dir / "result/protect_both_restore_6/trace_protect_both_Fetch_Commit_6.out.gz"
    # )
    # read_file(proj_dir / "result/protect_module_restore_0/trace_protect_module_Commit_0.out.gz")
    # read_file(proj_dir / "result/protect_module_restore_7/trace_protect_module_Commit_7.out.gz")
    comp_two_traces(
        proj_dir / "result/protect_module_restore_0/trace_protect_module_Commit_0.out.gz",
        proj_dir / "result/protect_module_restore_7/trace_protect_module_Commit_7.out.gz"
    )
    # comp_two_traces(
    #     Path("/tmp/trace_protect_module_Commit_0.out.gz"),
    #     Path("/tmp/trace_protect_module_Commit_7.out.gz")
    # )
    # comp_two_traces(
    #     proj_dir / "result/protect_both_restore_0/trace_protect_both_Branch_0.out.gz",
    #     proj_dir / "result/protect_both_restore_6/trace_protect_both_Branch_6.out.gz"
    # )
    # comp_two_traces(
    #     proj_dir / "result/protect_both_restore_0/trace_protect_both_RubyCache_0.out.gz",
    #     proj_dir / "result/protect_both_restore_6/trace_protect_both_RubyCache_6.out.gz"
    # )
    # read_file(proj_dir / "result/protect_both_restore_0/trace_protect_both_RubyCache_0.out.gz")
    # read_file(proj_dir / "result/protect_both_restore_6/trace_protect_both_RubyCache_6.out.gz")


if __name__ == '__main__':
    main()
