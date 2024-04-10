from pathlib import Path
import re

script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent
root_dir = proj_dir.parent


def extract_pc(line: str):
    x = re.match(r"(\d+)[-:]@@@ \(([\da-z]+)=>([\da-z]+)\)", line)
    if not x:
        return None
    addr = int(x.group(2), 16)
    return addr


def read_trace(input_path: Path):
    with input_path.open() as input_file:
        lines = input_file.readlines()

    trace = []
    last_pc = 0
    for line in lines:
        curr_pc = extract_pc(line)
        if curr_pc is None:
            continue
        if curr_pc != last_pc:
            trace.append(curr_pc)
            last_pc = curr_pc

    output_dir = input_path.parent
    output_name = input_path.name.split("-")[0] + "-ptrace.txt"
    with (output_dir / output_name).open(mode="w") as output_file:
        for x in trace:
            output_file.write(f"{hex(x)}\n")


def extract_syscall(input_path: Path):
    with input_path.open() as input_file:
        lines = input_file.readlines()

    trace = []
    print_lines = 50
    print_next = print_lines
    for line in lines:
        fun_name = line.strip().split()[-1]
        if fun_name == "do_sys_open":
            print_next = print_lines
            trace.append("")
        # if fun_name == "entry_SYSCALL_64":
        #     print_next = print_lines
        #     trace.append("")
        # if fun_name == "asm_exc_page_fault":
        #     print_next = 0
        #     continue
        # if print_next == print_lines:
        #     trace.append("")
        if print_next:
            trace.append(fun_name)
            print_next -= 1
        # if fun_name == "native_irq_return_iret":
        #     print_next = print_lines

    output_dir = input_path.parent
    output_name = input_path.name.split("-")[0] + "-syscall-ftrace.txt"
    with (output_dir / output_name).open(mode="w") as output_file:
        for x in trace:
            output_file.write(f"{x}\n")




def main():
    # read_trace(root_dir / "gem5-new" / "incorrect-pgrep.txt")
    # read_trace(root_dir / "gem5-new" / "correct-pgrep.txt")

    extract_syscall(root_dir / "gem5-new" / "incorrect-ftrace.txt")
    extract_syscall(root_dir / "gem5-new" / "correct-ftrace.txt")


if __name__ == '__main__':
    main()
