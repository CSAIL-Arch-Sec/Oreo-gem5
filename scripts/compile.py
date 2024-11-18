import click
import subprocess
from utils import *

@click.command()
@click.option(
    "--num-cores",
    type=click.INT,
    required=True,
)
def main(num_cores: int):
    build_ckpt_gem5 = f"echo \"\\ny\\n\" | scons build/X86_MOESI_hammer/gem5.fast -j{num_cores}"
    build_fast_gem5 = f"echo \"\\ny\\n\" | scons build/X86/gem5.fast -j{num_cores}"
    build_opt_gem5 = f"echo \"\\ny\\n\" | scons build/X86/gem5.opt -j{num_cores}"

    print(build_ckpt_gem5)
    subprocess.run(build_ckpt_gem5, shell=True, cwd=proj_dir)
    print(build_fast_gem5)
    subprocess.run(build_fast_gem5, shell=True, cwd=proj_dir)
    print(build_opt_gem5)
    subprocess.run(build_opt_gem5, shell=True, cwd=proj_dir)

    build_m5 = f"scons build/x86/out/m5"
    print(build_m5)
    subprocess.run(build_m5, shell=True, cwd=(proj_dir / "util/m5"))


if __name__ == '__main__':
    main()
