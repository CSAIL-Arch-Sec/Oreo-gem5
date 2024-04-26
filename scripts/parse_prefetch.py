from utils import *
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re


def read_file(input_path: Path, setup: str):
    with input_path.open(mode="r") as input_file:
        lines = input_file.readlines()

    result = []
    for line in lines:
        words = line.strip().split()
        if len(words) != 3 or words[0] != "!!!":
            continue
        addr = int(words[1], 16)
        time = int(words[2])
        result.append([addr, time])

    df = pd.DataFrame(result, columns=["Address", "Latency (Cycles)"])
    df["Setup"] = setup
    return df


def main():
    result_dir = proj_dir / "result"
    path0 = result_dir / "restore_ko_000_0c0c00" / "entrybleed_/board.pc.com_1.device"
    path1 = result_dir / "restore_ko_111_0c0c00" / "entrybleed_/board.pc.com_1.device"

    df0 = read_file(path0, "Baseline")
    df1 = read_file(path1, "Oreo")

    df = pd.concat([df0, df1])
    # print(df)
    df.reset_index(inplace=True)

    plt.figure(figsize=(30, 9))
    sns.set_theme(style="ticks", font_scale=4)
    ax = sns.lineplot(data=df, x="Address", y="Latency (Cycles)", hue="Setup",
                      linewidth=5)
    sns.move_legend(ax, "center right")
    ax.annotate('0xffffff8601800040, 29 cycles', xy=(0xffffff8601800040, 29), xytext=(0xffffff8801800040, 30),
                arrowprops=dict(facecolor='black', shrink=0.05))
    # xtick_list = [0xffffff8001800040, 0xffffff8601800040, 0xffffffee81800040]
    xtick_list = [0xffffff8001800040, 0xffffffee81800040]
    ax.set_xticks(xtick_list, list(map(hex, xtick_list)))
    plt.tight_layout()
    plt.savefig(script_dir / "plot" / "prefetch_plot.pdf")


if __name__ == '__main__':
    main()
