import click
import subprocess
from pathlib import Path


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent


@click.command()
@click.option(
    "--sim-option",
    type=click.Choice(['fast', 'opt']),
    default="fast"
)
@click.option(
    "--pre-setup",
    type=click.STRING,
)
@click.option(
    "--exp-script",
    type=click.STRING,
)
@click.option(
    "--debug-flags",
    type=click.STRING,
    default="None",
    # default="Branch,RubyCache,TLB,PageTableWalker,DRAM"
)
@click.option(
    "--gem5-kaslr-delta",
    type=int,
    default=0
)
@click.option(
    "--gem5-module-kaslr-delta",
    type=int,
    default=12
)
def main(
        sim_option: str,
        pre_setup: str,
        exp_script: str,
        debug_flags: str,
        gem5_kaslr_delta: int,
        gem5_module_kaslr_delta: int):
    gem5_str = f"./build/X86/gem5.{sim_option}"
    gem5_script = "configs/example/gem5_library/x86-ubuntu-run-example.py"
    starting_core = "kvm"
    
    protect_kaslr = ""
    protect_module_kaslr = ""
    protect_user_aslr = ""

    # TODO: Add more configs
    
    if pre_setup == "o3-module":
        output_dir_name = "protect_kaslr_module"
        switch_core = "o3"
        protect_kaslr = "--protect-kaslr"
        protect_module_kaslr = "--protect-module-kaslr"
    elif pre_setup == "o3-baseline":
        output_dir_name = "baseline_module"
        switch_core = "o3"
    elif pre_setup == "kvm":
        output_dir_name = "baseline"
        switch_core = "kvm"
    elif pre_setup == "kvm-module":
        output_dir_name = "baseline"
        switch_core = "kvm"
        protect_module_kaslr = "--protect-module-kaslr"
    elif pre_setup == "atomic":
        output_dir_name = "baseline"
        starting_core = "atomic"
        switch_core = "atomic"
    elif pre_setup == "o3":
        output_dir_name = "o3"
        starting_core = "o3"
        switch_core = "o3"
    elif pre_setup == "o3-text":
        output_dir_name = "o3_text"
        starting_core = "o3"
        switch_core = "o3"
        protect_kaslr = "--protect-kaslr"
    else:
        print(f"Pre-setup {pre_setup} is not support, aborting.")
        return

    output_dir = proj_dir / "result" / output_dir_name

    output_dir.mkdir(exist_ok=True)

    if debug_flags != "None":
        debug_option = f"--debug-flags={debug_flags}"
    else:
        debug_option = ""

    cmd = [
        "M5_OVERRIDE_PY_SOURCE=true",
        gem5_str,
        debug_option,
        f"--debug-file={output_dir}/trace.out.gz",
        f"--outdir={output_dir}",
        gem5_script,
        f"--starting-core={starting_core}",
        f"--switch-core={switch_core}",
        f"--script=/root/experiments/command-scripts/{exp_script}",
        protect_kaslr,
        protect_module_kaslr,
        protect_user_aslr,
        f"--gem5-kaslr-delta={gem5_kaslr_delta}",
        f"--gem5-module-kaslr-delta={gem5_module_kaslr_delta}",
    ]
    cmd_str = " ".join(cmd)
    print(cmd_str)

    output_path = output_dir / "output.log"
    output_path2 = output_dir / "output2.log"
    with output_path.open(mode="w") as output_file:
        with output_path2.open(mode="w") as output_file2:
            subprocess.run(
                cmd_str,
                shell=True,
                cwd=str(proj_dir),
                stdout=output_file,
                stderr=output_file2,
            )


if __name__ == '__main__':
    main()

