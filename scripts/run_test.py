import click
import subprocess
import numpy as np
from pathlib import Path


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent


def run(
        gem5_bin: Path, script_path: Path, output_dir: Path,
        protect_kaslr: bool = True,
        kaslr_offset: int = 0xc000000,
        cpu_type: str = "O3",
        switch_cpu: bool = False,
        switch_cpu_type: str = None,
        other_args: list = [],
        redirect_needed: bool = False,
        save_checkpoint: bool = True,
):
    output_dir.mkdir(exist_ok=True, parents=True)

    load_addr_offset = ~np.uint64(kaslr_offset) + np.uint64(1) + np.uint64(0x1000000)

    cmd = [
        "M5_OVERRIDE_PY_SOURCE=true",
        str(gem5_bin), f"--outdir={output_dir}",
        str(script_path),
        f"--kaslr-offset={kaslr_offset}",
        f"--load-addr-offset={load_addr_offset}",
    ]
    if protect_kaslr:
        cmd.append("--protect-kaslr")

    if save_checkpoint:
        cmd.append(f"--outputs-dir={output_dir}")

    if switch_cpu:
        if not switch_cpu_type:
            switch_cpu_type = cpu_type
        cmd.extend([
            f"--starting-core={cpu_type.lower()}",
            f"--switch-core={switch_cpu_type.lower()}",
        ])
    else:
        cmd.append(f"--cpu-type={cpu_type.upper()}")

    cmd.extend(other_args)

    output_log = output_dir / "output.log"
    if redirect_needed:
        cmd.extend([
            "--redirect-stderr",
            f"--stderr-file={output_log}",
            "--redirect-stdout",
            f"--stdout-file={output_log}",
        ])

    cmd_str = " ".join(cmd)
    print(cmd_str)

    with output_log.open(mode="w") as output_file:
        subprocess.run(
            cmd_str,
            shell=True,
            stdout=output_file,
            stderr=output_file
        )


@click.command()
@click.option("--save-checkpoint", is_flag=True)
def main(save_checkpoint: bool):
    # run(
    #     gem5_bin=(proj_dir / "build/X86_MOESI_hammer/gem5.fast"),
    #     script_path=(proj_dir / "configs/example/gem5_library/gem5-configs/x86-save.py"),
    #     output_dir=(proj_dir / "result" / "protect_kaslr_o3_checkpoint"),
    #     other_args=[
    #         "--checkpoint=1000000000000,100000000000,10",
    #         "--classic-cache",
    #     ],
    #     redirect_needed=True
    # )

    if save_checkpoint:
        run(
            gem5_bin=(proj_dir / "build/X86_MOESI_hammer/gem5.fast"),
            script_path=(proj_dir / "configs/example/gem5_library/gem5-configs/x86-save.py"),
            output_dir=(proj_dir / "result" / "protect_kaslr_o3_checkpoint"),
            other_args=[
                "--checkpoint=1000000000,1000000000,5",
                "--classic-cache",
            ],
            redirect_needed=True
        )
    else:
        checkpoint_dir = proj_dir / "result" / "protect_kaslr_o3_checkpoint" / "default-save/m5out-gen-cpt"
        checkpoint_tick = 10100000000
        run(
            gem5_bin=(proj_dir / "build/X86/gem5.fast"),
            # gem5_bin=(proj_dir / "build/X86_MOESI_hammer/gem5.fast"),
            script_path=(proj_dir / "configs/example/gem5_library/gem5-configs/x86-restore.py"),
            output_dir=(proj_dir / "result" / "protect_kaslr_o3_restore"),
            other_args=[
                f"--checkpoint-dir={checkpoint_dir}",
                f"--checkpoint-tick={checkpoint_tick}"
            ],
            redirect_needed=True,
            save_checkpoint=False,
        )


if __name__ == '__main__':
    main()
