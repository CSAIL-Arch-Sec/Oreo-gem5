from pathlib import Path

script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent


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
