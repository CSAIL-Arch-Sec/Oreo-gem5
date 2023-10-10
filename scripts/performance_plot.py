import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from utils import *


def parse_one_file(
        protect_mode: list,
        bench_id: int,
):
    result_path = proj_dir / "result" / f"{get_mode_name(*protect_mode)}_lebench_{bench_id}" / \
                  "m5out-default-restore" / "lebench_stats.csv"

    df = pd.read_csv(result_path)
    df["Setup"] = get_col_name(*protect_mode)
    df = df.set_index(["Setup", "name"])
    return df


def parse_all_files(mode_list: list, bench_list: list):
    df_list = []
    for protect_mode in mode_list:
        for bench_id in bench_list:
            df_list.append(parse_one_file(protect_mode, bench_id))

    df = pd.concat(df_list)
    print(df)
    return df


def main():
    mode_list = [
        [False, False],
        [True, True]
    ]
    bench_list = list(range(24))
    df = parse_all_files(mode_list, bench_list)

    ax = sns.barplot(x="name", y="mean (ns)", hue="Setup", data=df)
    plot_dir = proj_dir / "scripts" / "plot"
    plot_dir.mkdir(exist_ok=True)
    plt.savefig(plot_dir / "performance.pdf")


if __name__ == '__main__':
    main()
