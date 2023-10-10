import pandas as pd
import seaborn as sns
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
    print(df)


def parse_all_files(mode_list: list, bench_list: list):
    df_list = []
    for protect_mode in all_modes:
        for bench_id in bench_list:
            df_list.append(parse_one_file(protect_mode, bench_id))

    df = pd.concat(df_list)
    print(df)


def main():
    parse_one_file([False, False], 0)


if __name__ == '__main__':
    main()
