from utils import *
from pathlib import Path
import click
import multiprocessing
import uuid


def gen_one_checkpoint(
        core: str,
        protect_args: str,
        delta_args: str,
        add_checkpoint: str,
        use_uuid: bool,
        suffix: str,
):
    protect_arg_dict = gen_protect_args(protect_args)
    delta_arg_dict = gen_delta_args(delta_args)
    exp_script_path = Path("/root/experiments/command-scripts") / "exit_immediate.rcS"

    ret = run_one_test(
        sim_mode=SimMode.SAVE,
        sim_option="fast", debug_flags="",
        starting_core=core, switch_core=core,
        exp_script_path=exp_script_path,
        add_checkpoint=add_checkpoint,
        use_uuid=use_uuid,
        suffix=suffix,
        **protect_arg_dict,
        **delta_arg_dict,
    )

    if ret:
        print(f"Failed generating one checkpoint, ret = {ret}!!!")
    else:
        print("Successfully generating one checkpoint.")


def main():
    args_list = [
        # TODO: Use kvm generate checkpoint in the middle may help debug user aslr!
        # ["kvm", "1,1,0", "0,0,0", "", False, ""],
        # ["o3", "0,0,0", "c,6,0", "", True, ""],
        # ["o3", "0,0,0", "c,0,0", "", True, ""],
        # ["o3", "1,0,0", "c,0,0", "", True, ""],
        # ["o3", "0,1,0", "0,6,0", "", True, ""],
        ["o3", "1,1,0", "0,0,0", "", True, ""],
        # ["o3", "1,1,0", "c,0,0", "", True, ""],
        # ["o3", "1,1,0", "c,6,0", "", True, ""]
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(gen_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
