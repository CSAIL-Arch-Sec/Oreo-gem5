import click
import subprocess
from pathlib import Path


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent


@click.command()
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
def main(pre_setup: str, exp_script: str, debug_flags: str):
    gem5_str = "./build/X86/gem5.opt"
    gem5_script = "configs/example/gem5_library/x86-ubuntu-run-example.py"
    starting_core = "kvm"

    if pre_setup == "o3-module":
        output_dir_name = "protect_kaslr_module"
        switch_core = "o3"
        protect_module_kaslr = "--protect-module-kaslr"
    elif pre_setup == "o3-baseline":
        output_dir_name = "baseline_module"
        switch_core = "o3"
        protect_module_kaslr = ""
    elif pre_setup == "kvm":
        output_dir_name = "baseline"
        switch_core = "kvm"
        protect_module_kaslr = ""
    else:
        print(f"Pre-setup {pre_setup} is not support, aborting.")
        return

    output_dir = proj_dir / "result" / output_dir_name

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
        protect_module_kaslr
    ]
    cmd_str = " ".join(cmd)
    print(cmd_str)

    output_path = output_dir / "output.log"
    with output_path.open(mode="w") as output_file:
        subprocess.run(
            cmd_str,
            shell=True,
            cwd=str(proj_dir),
            stdout=output_file,
            stderr=output_file,
        )


if __name__ == '__main__':
    main()

