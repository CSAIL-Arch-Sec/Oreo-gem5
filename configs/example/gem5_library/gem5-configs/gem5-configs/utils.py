import os
import m5
import m5.core
import m5.options
from enum import Enum
import sys
import shutil
import m5.trace

# https://svn.blender.org/svnroot/bf-blender/trunk/blender/build_files/scons/tools/bcolors.py
class bcolors:
    HEADER = '\033[95m'  # magenta ?
    OKBLUE = '\033[94m'  # purple ?
    OKCYAN = '\033[96m'  # cyan
    OKGREEN = '\033[92m' # green
    WARNING = '\033[93m' # yellow
    FAIL = '\033[91m'    # red
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NONE = ''

class MessageType(Enum):
    DEFAULT = "[*]", bcolors.NONE, False, False
    MAGENTA = "[*]", bcolors.HEADER, False, True
    PURPLE = "[*]", bcolors.OKBLUE, False, True
    CYAN = "[*]", bcolors.OKCYAN, False, True
    GREEN = "[*]", bcolors.OKGREEN, False, True
    RED = "[*]", bcolors.WARNING, False, True
    MAGENTA_ = "[*]", bcolors.HEADER, False, False
    PURPLE_ = "[*]", bcolors.OKBLUE, False, False
    CYAN_ = "[*]", bcolors.OKCYAN, False, False
    GREEN_ = "[*]", bcolors.OKGREEN, False, False
    RED_ = "[*]", bcolors.WARNING, False, False
    YELLOW_ = "[*]", bcolors.FAIL, False, False
    WARNING = "[WARN]", bcolors.WARNING, False, True
    FAIL = "[FAIL]", bcolors.FAIL, False, True
    CHECKPOINT = "[CHCKPT]", bcolors.OKCYAN, False, True
    CONFIG = "[CONFIG]", bcolors.OKBLUE, False, False
    
def pretty_print(message: str, message_type: MessageType = MessageType.DEFAULT):
    lead_string, bcolor, is_bold, is_color = message_type.value
    endc = bcolors.ENDC
    bbold = bcolors.BOLD
    lead_string = bbold + bcolor + lead_string + endc + endc
    body_string = message
    if is_bold:
        body_string = bbold + body_string + endc
    if is_color:
        body_string = bcolor + body_string + endc
    print(f'{lead_string} {body_string}')

def test_pretty_print(message: str):
    for message_type in MessageType:
        pretty_print(message, message_type)


# https://stackoverflow.com/questions/185936/how-to-delete-the-contents-of-a-folder
def clear_dir(dir):
    for root, dirs, files in os.walk(dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def set_outdir(outdir):
    pretty_print(f"Setting output directory to: {outdir}")
    os.makedirs(outdir, exist_ok=True)
    clear_dir(outdir)
    m5.core.setOutputDir(outdir)
    m5.options.outdir = outdir

# parts from m5.main
def handle_std_redirects(args, output_dir):
    if args.redirect_stderr:
        stderr_file = args.stderr_file or os.path.join(output_dir, "sim_stderr")
        pretty_print(f"Redirecting stderr to: {stderr_file}")
        redir_fd = os.open(stderr_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.dup2(redir_fd, sys.stderr.fileno())
    if args.redirect_stdout:
        stderr_file = args.stderr_file or os.path.join(output_dir, "sim_stdout")
        pretty_print(f"Redirecting stdout to: {stderr_file}")
        redir_fd = os.open(stderr_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.dup2(redir_fd, sys.stderr.fileno())

def set_debug_file(args, output_dir):
    debug_file_path = args.debug_file or os.path.join(output_dir, "sim_debug")
    pretty_print(f"Saving debug trace to: {debug_file_path}")
    m5.trace.output(debug_file_path)
    m5.options.debug_file = debug_file_path