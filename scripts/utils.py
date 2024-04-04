import shutil
import uuid
from pathlib import Path
from enum import Enum
import subprocess

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


def get_core_args(sim_mode: SimMode, starting_core: str, switch_core: str):
    if sim_mode == SimMode.SIMPLE:
        return [f"--starting-core={starting_core.lower()}", f"--switch-core={switch_core.lower()}"]
    elif sim_mode == SimMode.SAVE:
        return [f"--cpu-type={starting_core.upper()}"]
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
    if suffix:
        dir_name_list.append(suffix)
    result = proj_dir / "result" / "_".join(dir_name_list)
    if sim_mode == SimMode.SAVE:
        if use_uuid:
            # result = result / str(uuid.uuid4())
            import arrow
            result = result / arrow.now().format("YYYY-MM-DD-HH-mm-ss")
        elif uuid_str:
            result = result / uuid_str
        else:
            result = result / "default"
    if sim_mode == SimMode.RESTORE:
        assert exp_script_name
        result = result / exp_script_name
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
        protect_kaslr: bool, protect_module_kaslr: bool, protect_user_aslr: bool,
        gem5_kaslr_delta: int, gem5_module_kaslr_delta: int, gem5_user_aslr_delta: int,
        exp_script_path: Path,
        add_checkpoint: str,
        use_uuid: bool, uuid_str: str, suffix: str
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
        "M5_OVERRIDE_PY_SOURCE=true",
        gem5_bin,
        debug_option,
        f"--debug-file={output_dir}/trace.out.gz",
        f"--outdir={output_dir}",
        gem5_script,
    ]

    cmd.extend(get_after_boot_script(sim_mode, exp_script_path))
    
    cmd.extend(get_core_args(sim_mode, starting_core, switch_core))

    if sim_mode != SimMode.RESTORE:
        # NOTE: Although we do not pass these args to the gem5 script, we still need them for
        # other purposes such as generating output directories.
        cmd.extend(get_protect_options(protect_kaslr, protect_module_kaslr, protect_user_aslr))

        cmd.extend([
            f"--gem5-kaslr-delta={gem5_kaslr_delta}",
            f"--gem5-module-kaslr-delta={gem5_module_kaslr_delta}",
            f"--gem5-user-aslr-delta={gem5_user_aslr_delta}",
        ])

    cmd.extend(get_checkpoint_args(
        sim_mode,
        starting_core, switch_core,
        protect_kaslr, protect_module_kaslr, protect_user_aslr,
        gem5_kaslr_delta, gem5_module_kaslr_delta, gem5_user_aslr_delta,
        add_checkpoint, uuid_str, suffix
    ))

    cmd_str = " ".join(cmd)
    print(cmd_str)

    ret = 0

    # return 0

    output_dir.mkdir(exist_ok=True, parents=True)
    for child in output_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)

    with stdout_path.open(mode="w") as stdout_file:
        with stderr_path.open(mode="w") as stderr_file:
            p = subprocess.run(
                cmd_str,
                shell=True,
                cwd=str(proj_dir),
                stdout=stdout_file,
                stderr=stderr_file,
            )
            ret = p.returncode

    return ret, output_dir


def gen_protect_args(input: str):
    data = list(map(lambda x: bool(int(x)), input.split(",")))
    return {
        "protect_kaslr": data[0],
        "protect_module_kaslr": data[1],
        "protect_user_aslr": data[2]
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
