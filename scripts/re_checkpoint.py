from utils import *
from pathlib import Path
import click
import multiprocessing


def re_one_checkpoint(
        sim_option: str, debug_flags: str,
        starting_core: str, swith_core: str,
        protect_args: str,  # Config protection option, baseline: "0,0,0", Oreo: "1,1,1"
        delta_args: str, # Config ASLR delta (for kernel only), the format is "delta,delta,0" for delta in [0, 221]
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
