import click
import multiprocessing
import numpy as np
import re
import subprocess
from pathlib import Path


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent
exp_dir = proj_dir.parent / "experiments"


def get_script_name(test_name: str, suffix):
    return f"security_test_{test_name}_{suffix}"


def gen_blindside_script(offset: int, after_boot_script_dir: Path):
    s = f"cd /home/gem5/experiments/modules\n" \
        f"insmod blindside-kernel.ko\n" \
        f"cd /home/gem5/experiments/bin\n" \
        f"./blindside 1 {offset}\n" \
        f"sleep 1\n" \
        f"m5 exit\n"

    # s = f"m5 exit\n"

    output_path = after_boot_script_dir / get_script_name("blindside", offset)
    with output_path.open(mode="w") as output_file:
        output_file.write(s)

    return output_path


def run_blindside_one(
        offset: int,
        protect_text: bool,
        protect_module: bool,
        debug_flags: str,
        debug_tick,
        debug_end_tick,
        checkpoint_dir: Path,
        after_boot_script_dir: Path,
        output_dir: Path,
        trace_name: str,
        kaslr_offset: int = 0xc000000,
        image_suffix: str = "",

):
    load_addr_offset = ~np.uint64(kaslr_offset) + np.uint64(1) + np.uint64(0x1000000)

    blind_script_path = gen_blindside_script(offset, after_boot_script_dir)

    if debug_flags != "None":
        debug_option = f"--debug-flags={debug_flags}"
    else:
        debug_option = ""

    if debug_tick is not None:
        debug_start = f"--debug-start={debug_tick}"
    else:
        debug_start = ""

    if debug_end_tick is not None:
        debug_end = f"--debug-end={debug_end_tick}"
    else:
        debug_end = ""

    gem5_str = "./build/X86/gem5.opt"
    gem5_script = "configs/example/gem5_library/gem5-configs/x86-restore.py"

    output_log = output_dir / "output.log"

    cmd = [
        "M5_OVERRIDE_PY_SOURCE=true",
        gem5_str,
        debug_option,
        debug_start,
        debug_end,
        f"--debug-file={output_dir}/{trace_name}.out.gz",
        f"--outdir={output_dir}",
        gem5_script,
        f"--kaslr-offset={kaslr_offset}",
        f"--load-addr-offset={load_addr_offset}",
        f"--script={blind_script_path}",
        "--cpu-type=O3",
        "--redirect-stderr",
        f"--stderr-file={output_log}",
        "--redirect-stdout",
        f"--stdout-file={output_log}",
        f"--checkpoint-dir={checkpoint_dir}",
        f"--outputs-dir={output_dir}"
    ]

    if protect_text:
        cmd.append("--protect-kaslr")

    if protect_module:
        cmd.append("--protect-module-kaslr")

    if image_suffix:
        cmd.append(f"--image-suffix={image_suffix}")

    cmd_str = " ".join(cmd)
    print(cmd_str)
    with output_log.open(mode="w") as output_file:
        subprocess.run(
            cmd_str,
            shell=True,
            cwd=str(proj_dir),
            stdout=output_file,
            stderr=output_file,
        )


def get_mode_name(protect_text: bool, protect_module: bool):
    if protect_text:
        if protect_module:
            return "protect_both"
        else:
            return "protect_text"
    else:
        if protect_module:
            return "protect_module"
        else:
            return "protect_none"


def test_one_setup(
        test_offset: int,
        protect_text: bool,
        protect_module: bool,
        checkpoint_dir_suffix: str,
        debug_flags: str,
        debug_tick: int,
        debug_end_tick: int,
        after_boot_script_dir: Path,
        image_suffix: str,

):
    mode_name = get_mode_name(protect_text, protect_module)

    checkpoint_dir = proj_dir / "result" / f"{mode_name}_checkpoint{image_suffix}{checkpoint_dir_suffix}" / "default-save" / "m5out-gen-cpt"
    output_dir = proj_dir / "result" / f"{mode_name}_restore{image_suffix}_{test_offset}"
    trace_name = f"trace_{mode_name}_{re.sub(r',', r'_', debug_flags)}{image_suffix}_{test_offset}"

    output_dir.mkdir(exist_ok=True)

    run_blindside_one(
        offset=test_offset,
        protect_text=protect_text,
        protect_module=protect_module,
        debug_flags=debug_flags,
        debug_tick=debug_tick,
        debug_end_tick=debug_end_tick,
        checkpoint_dir=checkpoint_dir,
        after_boot_script_dir=after_boot_script_dir,
        output_dir=output_dir,
        trace_name=trace_name,
        kaslr_offset=0xc000000,
        image_suffix=image_suffix,
    )


@click.command()
@click.option(
    "--debug-flags",
    type=click.STRING
)
def main(debug_flags: str):
    # debug_flags = "Branch,RubyCache,TLB,PageTableWalker,DRAM"
    # debug_flags = "RubyCache"
    after_boot_script_dir = script_dir / "after_boot"
    after_boot_script_dir.mkdir(exist_ok=True)

    args_list = [
        # [0, False, False, "_0", debug_flags, None, None, after_boot_script_dir, ""],
        # [0, False, False, "_0", debug_flags, None, None, after_boot_script_dir, "_6_16"],
        # [7, False, False, "_0", debug_flags, None, None, after_boot_script_dir, ""],
        # [7, False, False, "_0", debug_flags, None, None, after_boot_script_dir, "_6_16"],
        [0, False, True, "_0", debug_flags, 11443947038500, 11443947083000, after_boot_script_dir, ""],
        # [0, False, True, "_0", debug_flags, None, None, after_boot_script_dir, "_6_16"],
        [7, False, True, "_0", debug_flags, 11443947038500, 11443947083000, after_boot_script_dir, ""], # 11443947038500
        # [7, False, True, "_0", debug_flags, None, None, after_boot_script_dir, "_6_16"],
        # [16, False, True, "_0", debug_flags, None, None, after_boot_script_dir, ""],
        # [0, False, False, "_1", debug_flags, None, None, after_boot_script_dir, ""],
        # [6, False, False, "_1", debug_flags, None, None, after_boot_script_dir, ""],
        # [0, True, True, "_1", debug_flags, None, None, after_boot_script_dir, ""],
        # [6, True, True, "_1", debug_flags, None, None, after_boot_script_dir, ""],
    ]

    print(args_list)

    with multiprocessing.Pool(16) as p:
        p.starmap(test_one_setup, args_list)

    # test_offset = 7
    # protect_text = False
    # protect_module = True
    # mode_name = get_mode_name(protect_text, protect_module)
    #
    # checkpoint_dir = proj_dir / "result" / f"{mode_name}_checkpoint_0" / "default-save" / "m5out-gen-cpt"
    # output_dir = proj_dir / "result" / f"{mode_name}_restore_{test_offset}"
    # trace_name = f"trace_{mode_name}_{re.sub(r',', r'_', debug_flags)}"
    #
    # output_dir.mkdir(exist_ok=True)
    #
    # run_blindside_one(
    #     offset=test_offset,
    #     protect_text=protect_text,
    #     protect_module=protect_module,
    #     debug_flags=debug_flags,
    #     checkpoint_dir=checkpoint_dir,
    #     after_boot_script_dir=after_boot_script_dir,
    #     output_dir=output_dir,
    #     trace_name=trace_name,
    #     kaslr_offset=0xc000000,
    #     image_suffix="",
    # )


# def get_cpt_files():
#     file_list = [
#         "board.pc.com_1.device",
#         "board.pc.south_bridge.ide.disks.image.cow",
#         "board.physmem.store0.pmem",
#         "config.ini", "config.json",
#         "m5.cpt", "sim_debug", "stats.txt",
#     ]
#
#     cpt_folder_list = [
#         "protect_none_checkpoint_1",
#         "protect_both_checkpoint_1"
#     ]
#
#     for cpt_folder_name in cpt_folder_list:
#         cpt_dir = f"result/{cpt_folder_name}/default-save/m5out-gen-cpt/"
#         src_dir = "shixins@dobby.csail.mit.edu:/home/shixins/protect-kaslr/gem5/" + cpt_dir
#         dst_dir = proj_dir / cpt_dir
#
#         dst_dir.mkdir(exist_ok=True, parents=True)

        # scp shixins@dobby.csail.mit.edu:/home/shixins/protect-kaslr/gem5/result/protect_none_checkpoint_1/default-save/m5out-gen-cpt/protect_none.tar.gz .

        # for file_name in file_list:
        #     src_file = src_dir + file_name
        #     cmd = f"scp {src_file} {dst_dir}"
        #     print(cmd)
        #     subprocess.run(cmd, shell=True)



if __name__ == '__main__':
    main()


