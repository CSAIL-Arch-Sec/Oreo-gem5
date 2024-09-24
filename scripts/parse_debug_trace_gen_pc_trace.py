from pathlib import Path
import re
from utils import *


def parse_asm_file(asm_path: Path):
    with asm_path.open() as asm_file:
        lines = asm_file.readlines()

    result = {}
    curr_func_name = None
    curr_func_pc_list = None

    for line in lines:
        x = re.search(r"[a-f\d]{16} <(.+)>:", line)
        if x is not None:
            if curr_func_name is not None:
                assert curr_func_pc_list is not None
                result[curr_func_name] = curr_func_pc_list
            curr_func_name = x.group(1)
            curr_func_pc_list = []
            continue
        x = re.search(r"([a-f\d]+):\t", line)
        if x is not None:
            assert curr_func_name is not None
            assert curr_func_pc_list is not None
            curr_func_pc_list.append(int(x.group(1), 16))

    return result


def asm_func_lookup(asm_func_pc_map: dict, pc: int):
    for func_name, pc_list in asm_func_pc_map.items():
        if len(pc_list) > 0 and pc_list[0] <= pc <= pc_list[-1]:
            if pc in pc_list:
                return func_name

    return None


def parse_trace_one_line(line: str, begin_pc: int):
    x = re.search(r"\((0x[a-z\d]+)=>0x[a-z\d]+\)", line)
    if x is None:
        return None
    else:
        pc = int(x.group(1), 16)
        # begin_pc = 0x555555554000
        if begin_pc <= pc < begin_pc + 0x100000000000:
            new_pc = pc - begin_pc
            return new_pc
        else:
            return None


def sub_pc(line: str, new_pc: int):
    new_line = re.sub(
        r"\((0x[a-z\d]+)=>",
        f"({hex(new_pc)}=>",
        line
    )
    return new_line


def parse_trace_file(input_path: Path, output_path: Path, begin_pc: int):
    with input_path.open() as input_file:
        lines = input_file.readlines()

    result = []
    for line in lines:
        pc = parse_trace_one_line(line, begin_pc)
        if pc is not None:
            result.append(sub_pc(line, pc))

    with output_path.open(mode="w") as output_file:
        output_file.writelines(result)


def gen_func_trace(input_path: Path, output_path: Path, begin_pc: int, asm_func_pc_map: dict):
    with input_path.open() as input_file:
        lines = input_file.readlines()

    pc_trace = []
    for line in lines:
        pc = parse_trace_one_line(line, begin_pc)
        if pc is not None:
            pc_trace.append(pc)

    curr_func = None
    result = []
    for pc in pc_trace:
        func_name = asm_func_lookup(asm_func_pc_map, pc)
        if func_name is not None:
            if func_name != curr_func:
                print(f"{func_name} {hex(pc)}\n")
                # result.append(f"{func_name} {hex(pc)}\n")
                curr_func = func_name
        else:
            print("Cannot find func for pc", hex(pc))
            break

    # with output_path.open(mode="w") as output_file:
    #     output_file.writelines(result)
    # return result


def main():
    asm_path = Path("/home/shixinsong/Desktop/MIT/protect-kaslr/spec2017-result/benchspec/CPU/502.gcc_r/run/run_base_test_mytest-m64.0000/cpugcc_r_base.mytest-m64.asm")
    asm_func_pc_map = parse_asm_file(asm_path)
    # for func, pc_list in asm_func_pc_map.items():
    #     print(func)
    #     for pc in pc_list:
    #         print(hex(pc))

    # input_path = proj_dir / "result/simple_ko_000_000000/spec2017-502.gcc_r_/stdout.log"
    # output_path = proj_dir / "test-gcc-only.txt"
    # parse_trace_file(input_path, output_path)

    input_path = proj_dir / "test-gcc-only-partial.txt"
    output_path = proj_dir / "test-func-trace.txt"
    gen_func_trace(input_path, output_path, 0, asm_func_pc_map)


if __name__ == '__main__':
    main()
