from utils import *
from pathlib import Path
import click
import multiprocessing
import uuid


def gen_one_checkpoint(
        core: str,
        sim_cpu_cores: int,
        protect_args: str,
        delta_args: str,
        add_checkpoint: str,
        use_uuid: bool,
        suffix: str,
):
    protect_arg_dict = gen_protect_args(protect_args)
    delta_arg_dict = gen_delta_args(delta_args)
    exp_script_path = Path("/root/experiments/command-scripts") / "exit_immediate.rcS"

    ret, output_dir = run_one_test(
        sim_mode=SimMode.SAVE,
        sim_option="fast", debug_flags="",
        starting_core=core, switch_core=core,
        sim_cpu_cores=sim_cpu_cores,
        exp_script_path=exp_script_path,
        add_checkpoint=add_checkpoint,
        use_uuid=use_uuid,
        uuid_str="",
        suffix=suffix,
        **protect_arg_dict,
        **delta_arg_dict,
    )

    if ret:
        print(f"Failed generating one checkpoint, ret = {ret}!!!")
        return None
    else:
        print(f"Successfully generating one checkpoint {output_dir}")
        return output_dir


def main():
    args_list = [
        ["kvm", 1, "0,0,0", "c,c,0", "", False, ""],
        ["kvm", 1, "1,1,1", "c,c,0", "", False, ""],
    ]

    with multiprocessing.Pool(1) as p:
        p.starmap(gen_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
