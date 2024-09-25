import argparse

from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (MESITwoLevelCacheHierarchy,)
from gem5.components.processors.simple_switchable_processor import SimpleSwitchableProcessor
from gem5.coherence_protocol import CoherenceProtocol
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes, get_cpu_type_from_str
from gem5.resources.resource import KernelResource, DiskImageResource
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent


parser = argparse.ArgumentParser(
    description="An example configuration script to run the x86 ubuntu FS simulation."
)

parser.add_argument(
    "--protect-kaslr",
    action="store_true",
    help="Whether to protect KASLR.",
)

parser.add_argument(
    "--protect-module-kaslr",
    action="store_true",
    help="Whether to protect KASLR.",
)

parser.add_argument(
    "--protect-user-aslr",
    action="store_true",
    help="Whether to protect user ASLR.",
)

parser.add_argument(
    "--kaslr-offset",
    type=int,
    # default=0,
    default=0xffffff8080000000,
    # default=0xfffffe8680000000,
    help="KASLR offset.",
)

parser.add_argument(
    "--gem5-kaslr-align-bits",
    type=int,
    default=31,
    help="Text KASLR delta align bits.",
)

parser.add_argument(
    "--gem5-kaslr-delta",
    type=int,
    default=0,
    help="Text KASLR delta.",
)

parser.add_argument(
    "--gem5-module-kaslr-delta",
    type=int,
    default=0,
    help="Module KASLR delta.",
)

parser.add_argument(
    "--gem5-user-aslr-delta",
    type=int,
    default=0,
    help="User ASLR delta.",
)

# NOTE: We may keep load_addr_offset = 0 if we do not
#   do kaslr at link time. DOUBLE CHECK!
parser.add_argument(
    "--load-addr-offset",
    type=int,
    default=0,
    help="specify kernel physical load address offset"
)

parser.add_argument(
    "--image-suffix",
    type=str,
    default="",
    help="Kernel image suffix."
)

# Possible options:
#   atomic, kvm, o3, timing, minor, noncaching
parser.add_argument(
    "--starting-core",
    type=str,
    default="noncaching",
    help="Starting core type.",
)
parser.add_argument(
    "--switch-core",
    type=str,
    default="noncaching",
    help="Switch core type.",
)

parser.add_argument(
    "--cpu-cores",
    type=int,
    default=2,
    help="number of cpu cores for run"
)

parser.add_argument(
    "--disk-image-path",
    type=str,
    default="/root/experiments/disk-image/experiments.img",
    help="disk image path to use for run"
)
parser.add_argument(
    "--disk-root-partition",
    type=str,
    default="2",
    help="root partiton of disk image"
)

parser.add_argument(
    "--script",
    type=str,
    default="/root/experiments/command-scripts/exit_immediate.rcS",
    help="path to script to run"
)

args = parser.parse_args()

if args.protect_kaslr:
    protect_kaslr = True
else:
    protect_kaslr = False

if args.protect_module_kaslr:
    protect_module_kaslr = True
else:
    protect_module_kaslr = False

if args.protect_user_aslr:
    protect_user_aslr = True
else:
    protect_user_aslr = False

kaslr_offset = args.kaslr_offset + (args.gem5_kaslr_delta << args.gem5_kaslr_align_bits)
print("@@@ KASLR offset:", hex(kaslr_offset))

kernel_args_delta = [
    "--",
    f"gem5_module_kaslr_delta={args.gem5_module_kaslr_delta}",
    f"gem5_user_aslr_delta={args.gem5_user_aslr_delta}",
]
# if protect_module_kaslr or protect_user_aslr:
#     kernel_args_delta.append("--")
# if protect_module_kaslr:
#     kernel_args_delta.append(f"gem5_module_kaslr_delta={args.gem5_module_kaslr_delta}")
# if protect_user_aslr:
#     kernel_args_delta.append(f"gem5_user_aslr_delta={args.gem5_user_aslr_delta}")

starting_core = get_cpu_type_from_str(args.starting_core)
switch_core = get_cpu_type_from_str(args.switch_core)
print(starting_core)
print(switch_core)

# This runs a check to ensure the gem5 binary is compiled to X86 and supports
# the MESI Two Level coherence protocol.
requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    kvm_required=True,
)

# Here we setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="64KiB",
    l1d_assoc=8,
    l1i_size="64KiB",
    l1i_assoc=8,
    l2_size="2048kB",
    l2_assoc=16,
    num_l2_banks=1,
)

# Setup the system memory.
# Note, by default DDR3_1600 defaults to a size of 8GiB. However, a current
# limitation with the X86 board is it can only accept memory systems up to 3GB.
# As such, we must fix the size.
memory = DualChannelDDR4_2400(size="3GB")

# Here we setup the processor. This is a special switchable processor in which
# a starting core type and a switch core type must be specified. Once a
# configuration is instantiated a user may call `processor.switch()` to switch
# from the starting core types to the switch core types. In this simulation
# we start with KVM cores to simulate the OS boot, then switch to the Timing
# cores for the command we wish to run after boot.
processor = SimpleSwitchableProcessor(
    # starting_core_type=CPUTypes.NONCACHING,
    starting_core_type=starting_core,
    switch_core_type=switch_core,
    num_cores=args.cpu_cores,
    isa=ISA.X86,
    protect_kaslr=protect_kaslr,
    protect_module_kaslr=protect_module_kaslr,
    protect_user_aslr=protect_user_aslr,
    kaslr_offset=kaslr_offset,
)

# Here we setup the board. The X86Board allows for Full-System X86 simulations.
board = X86Board(
    clk_freq="2GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    load_addr_offset=args.load_addr_offset,
    kaslr_offset=kaslr_offset,
)

# This is the command to run after the system has booted. The first `m5 exit`
# will stop the simulation so we can switch the CPU cores from KVM to timing
# and continue the simulation to run the echo command, sleep for a second,
# then, again, call `m5 exit` to terminate the simulation. After simulation
# has ended you may inspect `m5out/system.pc.com_1.device` to see the echo
# output.
command = "m5 exit;" \
          + "echo 'This is running on O3 CPU cores.';" \
          + "head /proc/kallsyms;" \
          + "sleep 1; ls;" \
          + "m5 exit;"

# Here we set the Full System workload.
# The `set_workload` function for the X86Board takes a kernel, a disk image,
# and, optionally, a the contents of the "readfile". In the case of the
# "x86-ubuntu-18.04-img", a file to be executed as a script after booting the
# system.

# Support boot linux with kvm when protecting kernel text aslr
if starting_core == CPUTypes.KVM and protect_kaslr:
    image_suffix = "_kvm" + args.image_suffix
else:
    image_suffix = args.image_suffix

if protect_user_aslr:
    if protect_kaslr and protect_module_kaslr:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect_all" + image_suffix
    elif protect_kaslr:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect_text_user" + image_suffix
    elif protect_module_kaslr:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect_module_user" + image_suffix
    else:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect_user" + image_suffix
else:
    if protect_kaslr and protect_module_kaslr:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect_both" + image_suffix
    elif protect_kaslr:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect" + image_suffix
    elif protect_module_kaslr:
        kernel_local_path = "/root/linux/vmlinux_gem5_protect_module" + image_suffix
    else:
        kernel_local_path = "/root/linux/vmlinux_gem5" + image_suffix
board.set_kernel_disk_workload(
    kernel=
    # Resource("x86-linux-kernel-5.4.49",),
    KernelResource(
        local_path=kernel_local_path,
    ),
    # disk_image=Resource("x86-ubuntu-18.04-img"),
    disk_image=DiskImageResource(
        local_path=args.disk_image_path,
        root_partition=args.disk_root_partition
    ),
    # readfile_contents=command,
    readfile=args.script,
    kernel_args=[
        "earlyprintk=ttyS0",
        "console=ttyS0",
        "lpj=7999923",
        "root={root_value}",
        *kernel_args_delta
    ]
)

def dirty_fix():
    yield False

def handle_workbegin():
    print("Resetting stats at the start of ROI!")
    m5.stats.reset()
    yield False

def handle_workend():
    m5.stats.dump()
    print("Dump stats at the end of the ROI!")
    yield False

simulator = Simulator(
    board=board,
    on_exit_event={
        # Here we want override the default behavior for the first m5 exit
        # exit event. Instead of exiting the simulator, we just want to
        # switch the processor. The 2nd 'm5 exit' after will revert to using
        # default behavior where the simulator run will exit.
        ExitEvent.EXIT: (func() for func in [processor.switch]),
        ExitEvent.CHECKPOINT: dirty_fix(),
        ExitEvent.WORKBEGIN: handle_workbegin(),
        ExitEvent.WORKEND: handle_workend(),
    },
)

print("Start run")

simulator.run()

print("Finish run")
