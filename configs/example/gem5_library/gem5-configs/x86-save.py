import argparse
from pathlib import Path
from uuid import uuid4

from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import (
    SimpleProcessor,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import *
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent

from utils import *
from arguments import *
from exit_handlers import *

parser = argparse.ArgumentParser(
    description="configuration script for checkpoint generation",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

add_cpu_arguments(parser, default_type=CPUTypes.O3)
add_cache_arguments(parser)  # cache -- not actually sure this part works yet ;-;

# add_std_redirect_arguments(parser)
# add_debug_arguments(parser)

add_kernel_disk_arguments(parser)
add_kernel_phy_load_arguments(parser)

add_protect_kaslr_arguments(parser)

# add_uuid_dir_argument(parser)
add_checkpoint_save_arguments(parser)

# parse args blah

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
load_addr_offset = args.load_addr_offset
print("@@@ KASLR offset:", hex(kaslr_offset))
print("@@@ Physical load offset:", hex(load_addr_offset))

kernel_args_delta = [
    "--",
    f"gem5_module_kaslr_delta={args.gem5_module_kaslr_delta}",
    f"gem5_user_aslr_delta={args.gem5_user_aslr_delta}",
]
# kernel_args_delta = []
# if protect_module_kaslr or protect_user_aslr:
#     kernel_args_delta.append("--")
# if protect_module_kaslr:
#     kernel_args_delta.append(f"gem5_module_kaslr_delta={args.gem5_module_kaslr_delta}")
# if protect_user_aslr:
#     kernel_args_delta.append(f"gem5_user_aslr_delta={args.gem5_user_aslr_delta}")

# We check for the required gem5 build.

is_kvm_cpu = args.cpu_type == CPUTypes.KVM

requires(
    isa_required=ISA.X86,
    kvm_required=is_kvm_cpu,
)

if args.classic_cache:
    from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import \
        PrivateL1PrivateL2CacheHierarchy
    from gem5.coherence_protocol import CoherenceProtocol

    requires(
        coherence_protocol_required=CoherenceProtocol.ARM_MOESI_HAMMER
    )
    cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
        l1d_size="32kB",
        l1i_size="32kB",
        l2_size="256kB",
    )
    print("PrivateL1PrivateL2CacheHierarchy")
elif args.ruby_cache:
    from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import \
        MESITwoLevelCacheHierarchy
    from gem5.coherence_protocol import CoherenceProtocol

    requires(
        coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL
    )
    cache_hierarchy = MESITwoLevelCacheHierarchy(
        l1d_size="64KiB",
        l1d_assoc=8,
        l1i_size="32KiB",
        l1i_assoc=4,
        l2_size="2048kB",
        l2_assoc=16,
        num_l2_banks=1,
    )
    print("MESITwoLevelCacheHierarchy")
else:
    from gem5.components.cachehierarchies.classic.no_cache import NoCache

    cache_hierarchy = NoCache()
    print("NoCache")


# Memory: Dual Channel DDR4 2400 DRAM device.
# The X86 board only supports 3 GB of main memory.

memory = DualChannelDDR4_2400(size="3GB")

print("Setup processor with protect_kaslr =", protect_kaslr,
      "protect_module_kaslr=", protect_module_kaslr,
      "protect_user_aslr=", protect_user_aslr,
      "kaslr_offset =", kaslr_offset)
processor = SimpleProcessor(
    cpu_type=args.cpu_type,
    isa=ISA.X86,
    num_cores=1,
    protect_kaslr=protect_kaslr,
    protect_module_kaslr=protect_module_kaslr,
    protect_user_aslr=protect_user_aslr,
    kaslr_offset=kaslr_offset
)

# Here we setup the board. The X86Board allows for Full-System X86 simulations

board = X86Board(
    clk_freq="2GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    load_addr_mask=args.load_addr_mask,
    load_addr_offset=args.load_addr_offset,
    addr_check=args.addr_check,
    kaslr_offset=kaslr_offset,
)

# Support boot linux with kvm when protecting kernel text aslr
if is_kvm_cpu and protect_kaslr:
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

print("Kernel path:", kernel_local_path)
board.set_kernel_disk_workload(
    # The x86 linux kernel will be automatically downloaded to the
    # `~/.cache/gem5` directory if not already present.
    # kernel=args.kernel,
    kernel=CustomResource(
        local_path=kernel_local_path,
    ),
    # disk_image=Resource("x86-ubuntu-18.04-img"),
    disk_image=CustomDiskImageResource(
        local_path=args.disk_image_path,
        disk_root_partition=args.disk_root_partition
    ),
    kernel_args=[
        "earlyprintk=ttyS0",
        "console=ttyS0",
        "lpj=7999923",
        "root={root_value}",
        *kernel_args_delta
    ]
)

# if args.uuid_dir:
#     output_dir = os.path.join(args.outputs_dir, str(uuid4()), "m5out-gen-cpt")
# else:
#     output_dir = os.path.join(args.outputs_dir, "default-save", "m5out-gen-cpt")
# set_outdir(output_dir)
# print("Output dir:", output_dir)
#
# handle_std_redirects(args, output_dir)
# set_debug_file(args, output_dir)

# if args.checkpoint_dir:
#     checkpoint_path = Path(args.checkpoint_dir) / f"cpt.tick-{args.checkpoint_tick}"
#     print(checkpoint_path)
# else:
#     checkpoint_path = None
#     print("No checkpoint path, start from beginning")
simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.CHECKPOINT: handle_checkpoint(),
        ExitEvent.SCHEDULED_TICK: handle_scheduled_checkpoint(),
        # ExitEvent.WORKEND: handle_workend(),
    },
    # checkpoint_path=checkpoint_path
)

scheduled_ticks = set()

if args.checkpoint is not None:
    if args.cpu_type == CPUTypes.ATOMIC:
        raise argparse.ArgumentError("it seems like recording checkpoints with atomic cpu doesn't really work :((")
    if is_kvm_cpu:
        print(
            "kvm needs a bit of weird tick adjustment to match ??? but seems to work otherwise",
            MessageType.WARNING)

str_to_int_list = lambda x: [int(num) for num in x.split(',')]
checkpoint_groups = [str_to_int_list(list) for list in args.checkpoint]

for checkpoint_group in checkpoint_groups:
    group_len = len(checkpoint_group)
    first_tick = checkpoint_group[0]
    if group_len == 1:
        scheduled_ticks.add(first_tick)
    else:
        step_size = checkpoint_group[1] if group_len > 1 else first_tick
        step_count = checkpoint_group[2] if group_len > 2 else 10
        if group_len > 3:
            print(f"{checkpoint_group} has too many arguments specified, ignoring extras...",
                         MessageType.WARNING)
        last_tick = first_tick + step_size * step_count
        group_ticks = range(first_tick, last_tick, step_size)
        scheduled_ticks.update(group_ticks)

scheduled_ticks = list(scheduled_ticks)
if is_kvm_cpu:
    kvm_adjusted_ticks = []
    kvm_min_tick = 1000000000
    for tick in scheduled_ticks:
        if tick < kvm_min_tick:
            print(f"ignoring request for tick {tick}, can't schedule before tick {kvm_min_tick} with kvm ;-;",
                         MessageType.WARNING)
        else:
            kvm_adjusted_ticks.append(tick - kvm_min_tick)
    scheduled_ticks = kvm_adjusted_ticks

scheduled_ticks.sort()
for tick in scheduled_ticks:
    adjustment = kvm_min_tick if is_kvm_cpu else 0
    print(f'Scheduling checkpoint for tick {tick + adjustment}', MessageType.GREEN)

# for scheduled_tick in scheduled_ticks:
#     m5.scheduleTickExitAbsolute(scheduled_tick)

print("Starting simulation", MessageType.MAGENTA)

simulator.run(
    scheduled_ticks=scheduled_ticks
)

print("Done with the simulation", MessageType.MAGENTA)
