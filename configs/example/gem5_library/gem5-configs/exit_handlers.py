import m5
import os
from utils import *

def handle_checkpoint():
    while True:
        curTick = m5.curTick()
        pretty_print(
            f'Taking checkpoint at tick {curTick} -- this is end of boot...', 
            MessageType.CHECKPOINT
        )
        m5.checkpoint(m5.options.outdir)
        yield True

def handle_scheduled_checkpoint():
    while True:
        curTick = m5.curTick()
        subdir = f'cpt.tick-{curTick}'
        pretty_print(
            f'Taking checkpoint at tick {curTick}',
            MessageType.CHECKPOINT
        )
        m5.checkpoint(os.path.join(m5.options.outdir, subdir))
        # os.rename(
        #     os.path.join(m5.options.outdir, subdir, "m5.cpt"), 
        #     os.path.join(m5.options.outdir, f"m5.cpt.tick.{curTick}"))
        # os.rmdir(os.path.join(m5.options.outdir, subdir))
        yield False

def handle_workbegin():
    print("Resetting stats at the start of ROI!")
    m5.stats.reset()
    yield False

def handle_workend():
    m5.stats.dump()
    print("Dump stats at the end of the ROI!")
    yield False