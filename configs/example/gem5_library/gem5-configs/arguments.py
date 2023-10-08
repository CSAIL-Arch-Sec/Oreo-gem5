from gem5.components.processors.cpu_types import CPUTypes
from gem5.resources.resource import *

m5outs_default_dir = "/root/experiments/m5outs"


def add_std_redirect_arguments(parser):
    '''
    add arguments for redirecting stderr/stdout to file
    '''
    parser.add_argument(
        "--redirect-stderr",
        action="store_true",
        default=True,
        help="enable redirecting stderr to file"
    )
    parser.add_argument(
        "--no-redirect-stderr",
        dest="redirect-stderr",
        action="store_false",
        help="disable redirecting stderr to file"
    )
    parser.add_argument(
        "--stderr-file",
        type=str,
        default=None,
        help="specify file to redirect stderr to"
    )
    parser.add_argument(
        "--redirect-stdout",
        action="store_true",
        default=False,
        help="enable redirecting stdout to file"
    )
    parser.add_argument(
        "--no-redirect-stdout",
        dest="redirect-stdout",
        action="store_false",
        help="disable redirecting stdout to file"
    )
    parser.add_argument(
        "--stdout-file",
        type=str,
        default=None,
        help="specify file to redirect stdout to"
    )


def add_debug_arguments(parser):
    '''
    add arguments for saving debug trace to file
    '''
    parser.add_argument(
        '--debug-file',
        type=str,
        default=None,
        help="specify file to save debug trace to"
    )


def add_checkpoint_restore_arguments(parser):
    '''
    add arguments for configuring restoring from checkpoint
    '''
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=None,
        help="specify directory of checkpoint to restore from"
    )
    parser.add_argument(
        "--checkpoint-id",
        type=str,
        default=None,
        help="specify id of checkpoint to restore from"
    )
    parser.add_argument(
        "--checkpoint-tick",
        type=int,
        default=None,
        help="specify tick of checkpoint to restore from"
    )
    parser.add_argument(
        "--checkpoint-latest",
        action="store_true",
        default=False,
        help="enable automatic restoring from most recent checkpoint"
    )
    add_uuid_dir_argument(parser)


def add_checkpoint_save_arguments(parser):
    '''
    add arguments for configuring saving a checkpoint
    '''
    parser.add_argument(
        "--outputs-dir",
        type=str,
        default=m5outs_default_dir,
        help="specify output directory"
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        nargs='+',
        default="",
        help="specify ticks to schedule checkpoints at"
    )
    add_uuid_dir_argument(parser)


def add_uuid_dir_argument(parser):
    '''
    add arguments for enabling uuid saves (this is kinda clunky though ;-;)
    '''
    parser.add_argument(
        "--uuid-dir",
        action="store_true",
        default=False,
        help="enable uuid based output naming"
    )


def add_kernel_disk_arguments(parser):
    '''
    add arguments for kernel disk workload parameters
    '''
    parser.add_argument(
        "--kernel",
        type=lambda path: CustomResource(str(path)),
        default=Resource("x86-linux-kernel-5.4.49"),
        help="kernel to use for run"
    )
    parser.add_argument(
        "--disk-image-path",
        type=str,
        default="/root/experiments/disk-image/experiments/experiments-image/experiments",
        help="disk image path to use for run"
    )
    parser.add_argument(
        "--disk-root-partition",
        type=str,
        default="1",
        help="root partiton of disk image"
    )


def add_run_script_arguments(parser):
    '''
    add arguments for command script configuration
    '''
    parser.add_argument(
        "--script",
        type=str,
        default="/root/experiments/command-scripts/exit_immediate.rcS",
        help="path to script to run"
    )


def add_cpu_arguments(parser, default_type: CPUTypes):
    '''
    add arguments for cpu configuration
    '''
    parser.add_argument(
        "--cpu-type",
        type=lambda name: CPUTypes.__members__.get(str(name)),
        default=default_type,
        help="cpu type for simulation",
        choices=[type for _, type in CPUTypes.__members__.items()],
    )
    parser.add_argument(
        "--cpu-cores",
        type=int,
        default=1,
        help="number of cpu cores for run"
    )


def add_kernel_phy_load_arguments(parser):
    '''
    add arguments for configuring kernel physical load address
    '''
    val_to_int = lambda val: int(val, 0)
    parser.add_argument(
        "--load-addr-mask",
        type=val_to_int,
        default=0xFFFFFFFFFFFFFFFF,
        help="specify kernel physical load address mask"
    )
    parser.add_argument(
        "--load-addr-offset",
        type=val_to_int,
        default=0,
        help="specify kernel physical load address offset"
    )
    parser.add_argument(
        '--addr-check',
        action='store_true',
        default=True,
        help="enable kernel load address check"
    )
    parser.add_argument(
        '--no-addr-check',
        dest='addr_check',
        action='store_false',
        help="disable kernel load address check"
    )


def add_protect_kaslr_arguments(parser):
    parser.add_argument(
        "--protect-kaslr",
        action="store_true",
        help="Whether to protect KASLR.",
    )

    parser.add_argument(
        "--protect-module-kaslr",
        action="store_true",
        help="Whether to protect module KASLR.",
    )

    parser.add_argument(
        "--kaslr-offset",
        type=int,
        default=0xc000000,
        help="KASLR offset.",
    )

    parser.add_argument(
        "--image-suffix",
        type=str,
        default="",
        help="Kernel image suffix."
    )


def add_cache_arguments(parser):
    '''
    add arguments for configuring cache
    '''
    parser.add_argument(
        '--classic-cache',
        action='store_true',
        default=False,
        help="enable ruby cache"
    )
    # TODO: unsure if the MOESI_hammer actually worked or not
    # or actually is checkpointing with cache even needed??
    parser.add_argument(
        '--ruby-cache',
        action='store_true',
        default=False,
        help="enable ruby cache"
    )
