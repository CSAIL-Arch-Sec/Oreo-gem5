from utils import *
from pathlib import Path
import click
import multiprocessing


def re_one_checkpoint(
        sim_option: str, debug_flags: str,
        starting_core: str, swith_core: str,
        protect_args: str,
        delta_args: str,
        cpt_tick: int,
        uuid_str: str,
        suffix: str,
        exp_script_path: Path = None,
        clear_tlb_roi: bool = False,
):
    protect_arg_dict = gen_protect_args(protect_args)
    delta_arg_dict = gen_delta_args(delta_args)

    if exp_script_path is None:
        exp_script_path = Path("/root/experiments/command-scripts") / "exit_immediate.rcS"

    ret, _ = run_one_test(
        sim_mode=SimMode.RESTORE,
        sim_option=sim_option, debug_flags=debug_flags,
        starting_core=starting_core, switch_core=swith_core,
        sim_cpu_cores=0,
        exp_script_path=exp_script_path,
        add_checkpoint=(None if cpt_tick is None else str(cpt_tick)),
        use_uuid=False,
        uuid_str=uuid_str,
        suffix=suffix,
        clear_tlb_roi=clear_tlb_roi,
        **protect_arg_dict,
        **delta_arg_dict,
    )

    if ret:
        print(f"Failed restoring from one checkpoint, ret = {ret} {protect_args} {delta_args} {exp_script_path}!!!")
    else:
        print(f"Successfully restoring from one checkpoint {protect_args} {delta_args} {exp_script_path}.")


def get_script(module_delta: int, user_delta: int):
    script = (f"cd /home/gem5/experiments/modules\n"
              f"insmod set_protection.ko module_delta={module_delta} user_delta={user_delta}\n"
              # f"dmesg | tail -n10\n"
              f"lsmod\n"
              f"dmesg | tail -n10")

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"kmod_{user_delta}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def get_blindside_script(probe_module: int, delta: int):
    script = (f"cd /home/gem5/experiments/modules\n"
              f"insmod blindside_kernel.ko\n"
              f"/home/gem5/experiments/bin/blindside {probe_module} {delta:03}\n"
              # f"sleep 1\n"
              # f"echo {delta:03}\n"
              f"m5 exit")

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"blindside_{probe_module}_{delta:02x}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def get_leak2_syscall_script():
    script = (f"/home/gem5/experiments/bin/leak_path_2\n"
              f"m5 exit")

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"leak2_syscall.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    return output_path


def main():
    path0 = get_script(12, 0)
    path1 = get_script(12, 1)
    blindside_path_00 = get_blindside_script(1, 0)
    blindside_path_0c = get_blindside_script(1, 0xc)
    blindside_path_0d = get_blindside_script(1, 0xd)
    leak2_syscall_path = get_leak2_syscall_script()

    args_list = [
        # ["fast", "", "kvm", "o3", "0,0,0", "0,0,0", 500000000000, "", ""],
        # ["fast", "", "kvm", "o3", "1,1,0", "0,0,0", 2600000000000, "", ""],
        # ["fast", "", "o3", "o3", "1,1,0", "0,0,0", 310000000000, "2024-03-31-21-06-51", ""],
        # ["fast", "", "kvm", "o3", "1,1,0", "0,0,0", 470000000000, "default_backup", ""],
        # ["fast", "", "o3", "o3", "1,1,0", "c,6,0", 600000000000, "2024-04-01-05-03-45", ""],
        # ["fast", "", "o3", "o3", "1,1,0", "c,6,0", 600000000000, "2024-04-01-05-03-45", ""],
        # ["fast", "", "kvm", "kvm", "0,0,0", "c,0,0", None, "2024-04-05-05-23-35", "", Path("/root/experiments/command-scripts") / "insmod_test.rcS"],
        # ["fast", "", "kvm", "o3", "0,0,0", "0,0,0", None, "2024-04-07-06-49-23", "", Path("/root/experiments/command-scripts") / "insmod_test.rcS"],
        # ["fast", "", "kvm", "o3", "1,1,0", "c,0,0", None, "2024-04-07-06-49-23", "", Path("/root/experiments/command-scripts") / "insmod_test.rcS"],
        # ["fast", "", "kvm", "o3", "1,1,1", "c,0,0", None, "default", "", path0],
        # ["fast", "", "kvm", "o3", "1,1,1", "c,0,0", None, "default", "", path1],

        # ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_00],
        # ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_00],

        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_0c, True],
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_0d, True],
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_0c, True],
        ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_0d, True],

        # ["fast", "", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_0c],
        # ["fast", "", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", blindside_path_0d],

        # ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_00],
        # ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_0c],
        # ["fast", "", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", blindside_path_0d],

        # ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "0,0,0", "c,c,0", None, "default", "", leak2_syscall_path],
        # ["opt", "Branch,RubyCache,TLB,PageTableWalker,DRAM", "kvm", "o3", "1,1,1", "c,c,0", None, "default", "", leak2_syscall_path],
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
