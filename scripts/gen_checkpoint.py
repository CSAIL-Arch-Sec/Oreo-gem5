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
        # TODO: Use kvm generate checkpoint in the middle may help debug user aslr!
        # ["kvm", 1, "0,0,0", "0,0,0", "500000000000,100000000000,1", False, ""],
        # ["kvm", 1, "1,1,0", "0,0,0", "800000000000,100000000000,10", False, ""],
        # ["kvm", 1, "1,1,0", "0,0,0", "2500000000000,100000000000,5", False, ""],
        # ["kvm", 1, "0,0,0", "0,0,0", "", True, ""],
        # ["kvm", 1, "1,1,0", "c,0,0", "", True, ""],
        # ["kvm", 1, "1,1,1", "c,0,0", "", False, ""],
        # ["o3", 1, "0,0,0", "0,0,0", "", True, ""], # Failed after: PCI: CLS 0 bytes, default 64
        # ["o3", 1, "0,0,0", "c,6,0", "", True, ""], # Failed after: PCI: CLS 0 bytes, default 64
        # ["o3", 1, "0,0,0", "c,0,0", "", True, ""],
        # ["o3", 1, "1,0,0", "c,0,0", "", True, ""],
        # ["o3", 1, "0,1,0", "0,6,0", "", True, ""],
        # ["o3", 1, "1,1,0", "0,0,0", "", True, ""], # Failed after: PCI: CLS 0 bytes, default 64
        # ["o3", 1, "1,1,0", "c,0,0", "", True, ""],
        # ["o3", 1, "1,1,0", "c,6,0", "", True, ""] # Failed again!!!
        # ["o3", 1, "1,1,0", "0,0,0", "300000000000,10000000000,10", True, ""],
        # ["o3", 1, "1,1,0", "0,0,0", "", True, ""],

        # ["o3", 1, "0,0,0", "0,0,0", "500000000000,100000000000,20", True, ""],
        # ["o3", 1, "0,0,0", "c,6,0", "500000000000,100000000000,20", True, ""],
        # ["o3", 1, "1,1,0", "0,0,0", "500000000000,100000000000,20", True, ""],

        # ["o3", 1, "0,0,0", "c,6,0", "600000000000,100000000000,20", True, ""],
        # ["o3", 1, "1,1,0", "c,6,0", "600000000000,100000000000,20", True, ""],

        # ["kvm", 1, "0,0,0", "0,0,0", "", True, ""],
        # ["kvm", 1, "0,0,0", "c,0,0", "", True, ""],
        # ["kvm", 1, "1,1,0", "0,0,0", "", True, ""],
        # ["kvm", 1, "1,1,0", "c,0,0", "", True, ""],
        # ["kvm", 1, "1,1,1", "0,0,0", "", True, ""],
        # ["kvm", 1, "1,1,1", "2,0,0", "", True, ""],
        # ["kvm", 1, "1,1,1", "c,0,0", "", True, ""],

        ["kvm", 1, "0,0,0", "c,c,0", "", False, ""],
        ["kvm", 1, "1,1,1", "c,c,0", "", False, ""],
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(gen_one_checkpoint, args_list)


if __name__ == '__main__':
    main()
