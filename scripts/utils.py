import shutil
import uuid
from pathlib import Path
from enum import Enum
import subprocess
from tenacity import retry

script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent
lebench_result_name = "lebench_stats.csv"


performance_test_list = [
    "context-switch",
    "small-read",
    "med-read",
    "big-read",
    "small-write",
    "med-write",
    "large-write",
    "mmap",
    "munmap",
    "fork",
    "big-fork",
    "thread-create",
    "small-send",
    "big-send",
    "small-recv",
    "big-recv",
    "small-select",
    "big-select",
    "small-poll",
    "big-poll",
    "small-epoll",
    "big-epoll",
    "small-pagefault",
    "big-pagefault",
]


spec2006_bench_list = [
    "400.perlbench",
    "401.bzip2",
    "403.gcc",
    "410.bwaves",
    "416.gamess",
    "429.mcf",
    "433.milc",
    "435.gromacs",
    "436.cactusADM",
    "437.leslie3d",
    "444.namd",
    "445.gobmk",
    "447.dealII",
    "450.soplex",
    "453.povray",
    "454.calculix",
    "456.hmmer",
    "458.sjeng",
    "459.GemsFDTD",
    "462.libquantum",
    "464.h264ref",
    "465.tonto",
    "470.lbm",
    "471.omnetpp",
    "473.astar",
    "481.wrf",
    "482.sphinx3",
    "483.xalancbmk",
    "998.specrand",
    "999.specrand",
]

spec2017_all_bench_list = [
    "500.perlbench_r",
    "502.gcc_r",
    "503.bwaves_r",
    "505.mcf_r",
    "507.cactuBSSN_r",
    "508.namd_r",
    "510.parest_r",
    "511.povray_r",
    "519.lbm_r",
    "520.omnetpp_r",
    "521.wrf_r",
    "523.xalancbmk_r",
    "525.x264_r",
    "526.blender_r",
    "527.cam4_r",
    "531.deepsjeng_r",
    "538.imagick_r",
    "541.leela_r",
    "544.nab_r",
    "548.exchange2_r",
    "549.fotonik3d_r",
    "554.roms_r",
    "557.xz_r",
    "600.perlbench_s",
    "602.gcc_s",
    "603.bwaves_s",
    "605.mcf_s",
    "607.cactuBSSN_s",
    "619.lbm_s",
    "620.omnetpp_s",
    "621.wrf_s",
    "623.xalancbmk_s",
    "625.x264_s",
    "627.cam4_s",
    "628.pop2_s",
    "631.deepsjeng_s",
    "638.imagick_s",
    "641.leela_s",
    "644.nab_s",
    "648.exchange2_s",
    "649.fotonik3d_s",
    "654.roms_s",
    "657.xz_s",
    "996.specrand_fs",
    "997.specrand_fr",
    "998.specrand_is",
    "999.specrand_ir",
]

spec2017_intrate_bench_list = [
    "500.perlbench_r",
    "502.gcc_r",
    "505.mcf_r",
    "520.omnetpp_r",
    "523.xalancbmk_r",
    "525.x264_r",
    "531.deepsjeng_r",
    "541.leela_r",
    "548.exchange2_r",
    # "557.xz_r",
    "999.specrand_ir",
]


def get_col_name(protect_text: bool, protect_module: bool):
    if protect_text:
        if protect_module:
            return "Oreo"
        else:
            return "protect_text"
    else:
        if protect_module:
            return "protect_module"
        else:
            return "Baseline"


def get_mode_name(protect_text: bool, protect_module: bool, protect_user: bool):
    if protect_user:
        if protect_text:
            if protect_module:
                return "protect_all"
            else:
                return "protect_text_user"
        else:
            if protect_module:
                return "protect_module_user"
            else:
                return "protect_user"
    else:
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


class SimMode(Enum):
    SIMPLE = 0
    SAVE = 1
    RESTORE = 2


def get_gem5_bin(sim_mode: SimMode, sim_option: str):
    if sim_mode == SimMode.SAVE:
        setup = "X86_MOESI_hammer"
    else:
        setup = "X86"
    return proj_dir / "build" / setup / f"gem5.{sim_option}"


def get_gem5_script(sim_mode: SimMode):
    if sim_mode == SimMode.SIMPLE:
        return proj_dir / "configs/example/gem5_library/x86-ubuntu-run-example.py"
    elif sim_mode == SimMode.SAVE:
        return proj_dir / "configs/example/gem5_library/gem5-configs/x86-save.py"
    else:
        return proj_dir / "configs/example/gem5_library/gem5-configs/x86-restore.py"


def get_core_args(sim_mode: SimMode, starting_core: str, switch_core: str, sim_cpu_cores: int):
    if sim_mode == SimMode.SIMPLE:
        return [f"--starting-core={starting_core.lower()}", f"--switch-core={switch_core.lower()}",
                f"--cpu-cores={sim_cpu_cores}"]
    elif sim_mode == SimMode.SAVE:
        return [f"--cpu-type={starting_core.upper()}", f"--cpu-cores={sim_cpu_cores}"]
    else:
        return [f"--cpu-type={switch_core.upper()}"]
    

def get_checkpoint_args(
        sim_mode: SimMode,
        starting_core: str, switch_core: str,
        protect_kaslr: bool, protect_module_kaslr: bool, protect_user_aslr: bool,
        gem5_kaslr_delta: int, gem5_module_kaslr_delta: int, gem5_user_aslr_delta: int,
        add_checkpoint: str, uuid_str: str, suffix: str,
):
    if sim_mode == SimMode.SIMPLE:
        return []
    elif sim_mode == SimMode.SAVE:
        result = ["--classic-cache"]
        if add_checkpoint:
            result.append(f"--checkpoint={add_checkpoint}")
        return result
    elif sim_mode == SimMode.RESTORE:
        checkpoint_dir = get_output_dir(
            SimMode.SAVE,
            starting_core, starting_core,
            protect_kaslr, protect_module_kaslr, protect_user_aslr,
            gem5_kaslr_delta, gem5_module_kaslr_delta, gem5_user_aslr_delta,
            "",
            False, uuid_str, suffix
        )
        result = [f"--checkpoint-dir={checkpoint_dir}"]
        if add_checkpoint:
            # NOTE: This is a bit dirty since add_checkpoint may have different formulas when used for save and restore.
            # For this case, it must be an integer.
            result.append(f"--checkpoint-tick={int(add_checkpoint)}")
        return result


def get_after_boot_script(sim_mode: SimMode, exp_script_path: Path):
    if sim_mode == SimMode.SAVE:
        return []
    else:
        return [f"--script={exp_script_path}"]


def get_output_dir(
        sim_mode: SimMode,
        starting_core: str, switch_core: str,
        protect_kaslr: bool, protect_module_kaslr: bool, protect_user_aslr: bool,
        gem5_kaslr_delta: int, gem5_module_kaslr_delta: int, gem5_user_aslr_delta: int,
        exp_script_name: str,
        use_uuid: bool, uuid_str: str, suffix: str
):
    dir_name_list = [
        sim_mode.name.lower(),
        f"{starting_core.lower()[0]}{switch_core.lower()[0]}",
        f"{int(protect_kaslr)}{int(protect_module_kaslr)}{int(protect_user_aslr)}",
        f"{gem5_kaslr_delta:02x}{gem5_module_kaslr_delta:02x}{gem5_user_aslr_delta:02x}",
    ]
    # if suffix:
    #     dir_name_list.append(suffix)
    result = proj_dir / "result" / "_".join(dir_name_list)
    if sim_mode == SimMode.SAVE:
        if use_uuid:
            # result = result / str(uuid.uuid4())
            import arrow
            subdir_name = arrow.now().format("YYYY-MM-DD-HH-mm-ss")
        elif uuid_str:
            subdir_name = uuid_str
        else:
            subdir_name = "default"
        if suffix:
            result = result / f"{subdir_name}_{suffix}"
        else:
            result = result / subdir_name
    if sim_mode == SimMode.RESTORE or sim_mode == SimMode.SIMPLE:
        assert exp_script_name
        result = result / f"{exp_script_name}_{suffix}"
    return result


def get_protect_options(protect_kaslr: bool, protect_module_kaslr: bool, protect_user_aslr: bool):
    result = []
    if protect_kaslr:
        result.append("--protect-kaslr")
    if protect_module_kaslr:
        result.append("--protect-module-kaslr")
    if protect_user_aslr:
        result.append("--protect-user-aslr")
    return result


def run_one_test(
        sim_mode: SimMode,
        sim_option: str, debug_flags: str,
        starting_core: str, switch_core: str,
        sim_cpu_cores: int,
        protect_kaslr: bool, protect_module_kaslr: bool, protect_user_aslr: bool,
        gem5_kaslr_delta: int, gem5_module_kaslr_delta: int, gem5_user_aslr_delta: int,
        exp_script_path: Path,
        add_checkpoint: str,
        use_uuid: bool, uuid_str: str, suffix: str,
        clear_tlb_roi: bool = False,
):
    if sim_option not in ["fast", "opt"]:
        print(f"Error: sim option {sim_option} is not supported!!!")
        return -1

    gem5_bin = str(get_gem5_bin(sim_mode, sim_option))
    gem5_script = str(get_gem5_script(sim_mode))

    if debug_flags != "":
        if sim_option == "fast":
            print("Error: gem5.fast does not support run with debug flags!")
            return -1
        debug_option = f"--debug-flags={debug_flags}"
    else:
        debug_option = ""

    output_dir = get_output_dir(
        sim_mode,
        starting_core, switch_core,
        protect_kaslr, protect_module_kaslr, protect_user_aslr,
        gem5_kaslr_delta, gem5_module_kaslr_delta, gem5_user_aslr_delta,
        exp_script_path.stem,
        use_uuid, "", suffix
    )
    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"

    cmd = [
        # "M5_OVERRIDE_PY_SOURCE=true",
        gem5_bin,
        debug_option,
        f"--debug-file={output_dir}/trace.out.gz",
        f"--outdir={output_dir}",
        gem5_script,
    ]

    cmd.extend(get_after_boot_script(sim_mode, exp_script_path))
    
    cmd.extend(get_core_args(sim_mode, starting_core, switch_core, sim_cpu_cores))

    if sim_mode != SimMode.RESTORE:
        # NOTE: Although we do not pass these args to the gem5 script, we still need them for
        # other purposes such as generating output directories.
        cmd.extend(get_protect_options(protect_kaslr, protect_module_kaslr, protect_user_aslr))

        cmd.extend([
            f"--gem5-kaslr-delta={gem5_kaslr_delta}",
            f"--gem5-module-kaslr-delta={gem5_module_kaslr_delta}",
            f"--gem5-user-aslr-delta={gem5_user_aslr_delta}",
        ])

    if clear_tlb_roi:
        cmd.append("--clear-tlb-roi")

    cmd.extend(get_checkpoint_args(
        sim_mode,
        starting_core, switch_core,
        protect_kaslr, protect_module_kaslr, protect_user_aslr,
        gem5_kaslr_delta, gem5_module_kaslr_delta, gem5_user_aslr_delta,
        add_checkpoint, uuid_str, ""
    ))

    cmd_str = " ".join(cmd)
    print(cmd_str)

    ret = 0

    # return 0

    output_dir.mkdir(exist_ok=True, parents=True)
    for child in output_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)

    if sim_mode == SimMode.SAVE and starting_core == "kvm":
        timeout = 180
    else:
        timeout = None

    @retry()
    def run():
        with stdout_path.open(mode="w") as stdout_file:
            with stderr_path.open(mode="w") as stderr_file:
                p = subprocess.Popen(
                    "exec " + cmd_str,
                    shell=True,
                    cwd=str(proj_dir),
                    stdout=stdout_file,
                    stderr=stderr_file,
                )
                try:
                    p.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    p.kill()
                    print(f"Run {output_dir} failed!!!")
                    raise
                ret = p.returncode
        return ret

    ret = run()

    return ret, output_dir


def gen_protect_args(input: str):
    data = list(map(lambda x: bool(int(x)), input.split(",")))
    return {
        "protect_kaslr": data[0],
        "protect_module_kaslr": data[1],
        "protect_user_aslr": data[2] # NOTE: this argument is deparated
    }


def gen_delta_args(input: str):
    data = list(map(lambda x: int(x, 16), input.split(",")))
    return {
        "gem5_kaslr_delta": data[0],
        "gem5_module_kaslr_delta": data[1],
        "gem5_user_aslr_delta": data[2]
    }


def get_lebench_script_name(bench_id: int):
    return f"lebench_{bench_id}"
