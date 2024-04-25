from utils import *
from pathlib import Path
import click
import multiprocessing


def switch_simple(
        starting_core: str, swith_core: str,
        protect_args: str,
        delta_args: str,
        use_uuid: bool,
        exp_script_path: Path
):
    protect_arg_dict = gen_protect_args(protect_args)
    delta_arg_dict = gen_delta_args(delta_args)

    ret, output_dir = run_one_test(
        sim_mode=SimMode.SIMPLE,
        sim_option="fast", debug_flags="",
        starting_core=starting_core, switch_core=swith_core,
        sim_cpu_cores=1,
        exp_script_path=exp_script_path,
        add_checkpoint="",
        use_uuid=use_uuid,
        uuid_str="",
        suffix="",
        **protect_arg_dict,
        **delta_arg_dict,
    )

    if ret:
        print(f"Failed run with switch core {starting_core}->{swith_core}, ret = {ret}!!!")
        return None
    else:
        print(f"Successfully generating one checkpoint with switch core {starting_core}->{swith_core}.")
        return output_dir


def main():
    script = (f"m5 exit\n"
              f"cd /home/gem5/experiments/modules\n"
              f"insmod set_protection.ko module_delta=12 user_delta=0\n"
              f"lsmod\n"
              f"dmesg | tail -n300\n"
              f"sleep 100")

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "insmod_test.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    args_list = [
        ["kvm", "kvm", "0,0,0", "0,0,0", False, output_path]
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(switch_simple, args_list)


if __name__ == '__main__':
    main()
