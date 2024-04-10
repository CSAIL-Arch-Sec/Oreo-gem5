from utils import *
from pathlib import Path
import click
import multiprocessing


def re_one_checkpoint(
        starting_core: str, swith_core: str,
        protect_args: str,
        delta_args: str,
        cpt_tick: int,
        uuid_str: str,
        suffix: str,
        exp_script_path: Path = None
):
    protect_arg_dict = gen_protect_args(protect_args)
    delta_arg_dict = gen_delta_args(delta_args)

    if exp_script_path is None:
        exp_script_path = Path("/root/experiments/command-scripts") / "exit_immediate.rcS"

    ret, _ = run_one_test(
        sim_mode=SimMode.RESTORE,
        sim_option="fast", debug_flags="",
        starting_core=starting_core, switch_core=swith_core,
        exp_script_path=exp_script_path,
        add_checkpoint=(None if cpt_tick is None else str(cpt_tick)),
        use_uuid=False,
        uuid_str=uuid_str,
        suffix=suffix,
        **protect_arg_dict,
        **delta_arg_dict,
    )

    if ret:
        print(f"Failed restoring from one checkpoint, ret = {ret}!!!")
    else:
        print("Successfully restoring from one checkpoint.")


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


def main():
    path0 = get_script(12, 0)
    path1 = get_script(12, 1)

    args_list = [
        # ["kvm", "o3", "0,0,0", "0,0,0", 500000000000, "", ""],
        # ["kvm", "o3", "1,1,0", "0,0,0", 2600000000000, "", ""],
        # ["o3", "o3", "1,1,0", "0,0,0", 310000000000, "2024-03-31-21-06-51", ""],
        # ["kvm", "o3", "1,1,0", "0,0,0", 470000000000, "default_backup", ""],
        # ["o3", "o3", "1,1,0", "c,6,0", 600000000000, "2024-04-01-05-03-45", ""],
        # ["o3", "o3", "1,1,0", "c,6,0", 600000000000, "2024-04-01-05-03-45", ""],
        # ["kvm", "kvm", "0,0,0", "c,0,0", None, "2024-04-05-05-23-35", "", Path("/root/experiments/command-scripts") / "insmod_test.rcS"],
        # ["kvm", "o3", "0,0,0", "0,0,0", None, "2024-04-07-06-49-23", "", Path("/root/experiments/command-scripts") / "insmod_test.rcS"],
        # ["kvm", "o3", "1,1,0", "c,0,0", None, "2024-04-07-06-49-23", "", Path("/root/experiments/command-scripts") / "insmod_test.rcS"],
        # ["kvm", "o3", "1,1,1", "c,0,0", None, "default", "", path0],
        ["kvm", "o3", "1,1,1", "c,0,0", None, "default", "", path1],

    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(re_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
