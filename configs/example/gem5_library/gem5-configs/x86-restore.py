import argparse
import json
import os
import sys
from uuid import uuid4
import glob

from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.processors.simple_processor import (
    SimpleProcessor,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.resources.resource import *
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent

from utils import *
from arguments import *
from exit_handlers import *

parser = argparse.ArgumentParser(
    description="configuration script for checkpoint restore",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

add_cpu_arguments(parser, default_type=CPUTypes.O3)

add_run_script_arguments(parser)

add_checkpoint_restore_arguments(parser)

args = parser.parse_args()

# if args.protect_kaslr:
#     protect_kaslr = True
# else:
#     protect_kaslr = False
#
# if args.protect_module_kaslr:
#     protect_module_kaslr = True
# else:
#     protect_module_kaslr = False
#
# if args.protect_user_aslr:
#     protect_user_aslr = True
# else:
#     protect_user_aslr = False

# kaslr_offset = args.kaslr_offset + (args.gem5_kaslr_delta << args.gem5_kaslr_align_bits)
# load_addr_offset = args.load_addr_offset
# print("@@@ KASLR offset:", hex(kaslr_offset))
# print("@@@ Physical load offset:", hex(load_addr_offset))

# kernel_args_delta = []
# if protect_module_kaslr or protect_user_aslr:
#     kernel_args_delta.append("--")
# if protect_module_kaslr:
#     kernel_args_delta.append(f"gem5_module_kaslr_delta={args.gem5_module_kaslr_delta}")
# if protect_user_aslr:
#     kernel_args_delta.append(f"gem5_user_aslr_delta={args.gem5_user_aslr_delta}")

pretty_print("Checking for required gem5 build...")
requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    # coherence_protocol_required=CoherenceProtocol.ARM_MOESI_HAMMER,
)

# things for reading generated checkpoint config

if not (args.checkpoint_dir or args.checkpoint_id):
    if args.checkpoint_latest:
        pretty_print('No checkpoint specified, using most recent from default save location...',
                     MessageType.CHECKPOINT)
        checkpoint_parent_dir = max(glob.iglob(f"{m5outs_default_dir}/*"), key=os.path.getctime)
        checkpoint_dir = os.path.join(checkpoint_parent_dir, "m5out-gen-cpt")
    else:
        pretty_print('No checkpoint specified, using default from default save location...',
                     MessageType.CHECKPOINT)
        checkpoint_dir = os.path.join(m5outs_default_dir, "default-save", "m5out-gen-cpt")
elif args.checkpoint_dir and args.checkpoint_id:
    pretty_print('Only one of checkpoint-dir and checkpoint-id should be specified :(',
                 MessageType.FAIL)
    parser.error('Please specify only one of --checkpoint-dir or --checkpoint-id, thanks :D')
else:
    checkpoint_dir = args.checkpoint_dir or \
                     os.path.join(m5outs_default_dir, args.checkpoint_id, "m5out-gen-cpt")

checkpoint_path = checkpoint_dir
if args.checkpoint_tick is not None:
    pretty_print(f'Checkpoint tick specified: cpt.tick-{args.checkpoint_tick} will be used instead of default...',
                 MessageType.CHECKPOINT)
    checkpoint_path = os.path.join(checkpoint_path, f'cpt.tick-{args.checkpoint_tick}')
pretty_print(f'Using checkpoint at {checkpoint_path}/m5.cpt', MessageType.CHECKPOINT)

config_dir = os.path.join(checkpoint_dir, "config.json")
pretty_print(f'Reading configuration from: {config_dir}', MessageType.CONFIG)
with open(config_dir) as f:
    config = json.load(f)

cpu_cores = len(config.get("board").get("processor").get("cores"))
kernel_path = config.get("board").get("workload").get("object_file")
load_addr_mask = config.get("board").get("workload").get("load_addr_mask")
load_addr_offset = config.get("board").get("workload").get("load_addr_offset")
addr_check = config.get("board").get("workload").get("addr_check")

disk_image_paths = [disk.get("image").get("child").get("image_file") for disk in \
                    config.get("board").get("pc").get("south_bridge").get("ide").get("disks")]
if len(disk_image_paths) != 1:
    sys.exit("for now we are only dealing with single disk image ;-;")
disk_image_path = disk_image_paths[0]

cores_info = config.get("board").get("processor").get("cores")
assert len(cores_info) > 0
core_info = cores_info[0].get("core")
protect_kaslr = core_info.get("protectKaslr")
protect_module_kaslr = core_info.get("protectModuleKaslr")
protect_user_aslr = core_info.get("protectUserAslr")

kaslr_offset = config.get("board").get("workload").get("kaslr_offset")
kernel_args = config.get("board").get("workload").get("command_line")

pretty_print(f'           num_cores: {cpu_cores}', MessageType.CONFIG)
pretty_print(f'         kernel_path: {kernel_path}', MessageType.CONFIG)
pretty_print(f'      load_addr_mask: {hex(load_addr_mask)}', MessageType.CONFIG)
pretty_print(f'    load_addr_offset: {hex(load_addr_offset)}', MessageType.CONFIG)
pretty_print(f'          addr_check: {"enabled" if addr_check else "disabled"}', MessageType.CONFIG)
pretty_print(f'     disk_image_path: {disk_image_path}', MessageType.CONFIG)
pretty_print(f'       protect_kaslr: {protect_kaslr}', MessageType.CONFIG)
pretty_print(f'protect_module_kaslr: {protect_module_kaslr}', MessageType.CONFIG)
pretty_print(f'   protect_user_aslr: {protect_user_aslr}', MessageType.CONFIG)
pretty_print(f'        kaslr_offset: {hex(kaslr_offset)}', MessageType.CONFIG)
pretty_print(f'         kernel_args: {kernel_args}', MessageType.CONFIG)

pretty_print("Setting up fixed system parameters...")

pretty_print("Caches: MESI Two Level Cache Hierarchy")

# from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
#     MESITwoLevelCacheHierarchy,
# )
#
# cache_hierarchy = MESITwoLevelCacheHierarchy(
#     l1d_size="64kB",
#     l1d_assoc=8,
#     l1i_size="32kB",
#     l1i_assoc=4,
#     l2_size="2048kB",
#     l2_assoc=16,
#     num_l2_banks=1,
# )
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import \
    PrivateL1PrivateL2CacheHierarchy
from gem5.coherence_protocol import CoherenceProtocol

requires(
    coherence_protocol_required=CoherenceProtocol.ARM_MOESI_HAMMER
)
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="128kB",
    l1i_size="128kB",
    l2_size="2048kB",
)
print("PrivateL1PrivateL2CacheHierarchy")

pretty_print("Memory: Dual Channel DDR4 2400 DRAM device")
# The X86 board only supports 3 GB of main memory.
from gem5.components.memory import DualChannelDDR4_2400

memory = DualChannelDDR4_2400(size="3GB")

processor = SimpleProcessor(
    cpu_type=args.cpu_type,
    isa=ISA.X86,
    num_cores=cpu_cores,
    protect_kaslr=protect_kaslr,
    protect_module_kaslr=protect_module_kaslr,
    protect_user_aslr=protect_user_aslr,
    kaslr_offset=kaslr_offset
)

board = X86Board(
    clk_freq="2GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    load_addr_mask=load_addr_mask,
    load_addr_offset=load_addr_offset,
    addr_check=addr_check,
    kaslr_offset=kaslr_offset,
)

board.set_kernel_disk_workload(
    kernel=CustomResource(
        local_path=kernel_path
    ),
    # disk_image=Resource("x86-ubuntu-18.04-img"),
    disk_image=CustomDiskImageResource(
        local_path=disk_image_path,
        disk_root_partition=args.disk_root_partition
    ),
    readfile=args.script,
    kernel_args=[kernel_args]
)
pretty_print(f"Script: {args.script}")

def dirty_fix():
    yield False


simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.CHECKPOINT: dirty_fix(),
        ExitEvent.WORKBEGIN: handle_workbegin(),
        ExitEvent.WORKEND: handle_workend(),
    },
    checkpoint_path=checkpoint_path,
)

pretty_print("Starting simulation...", MessageType.MAGENTA)

simulator.run()

pretty_print("Done with the simulation", MessageType.MAGENTA)
