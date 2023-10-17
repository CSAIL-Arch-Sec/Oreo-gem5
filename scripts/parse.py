from pathlib import Path
import pandas as pd
import numpy as np
from utils import *
import re


pattern = re.compile(r"^protect_(\w+)_lebench_random_(\d+)$")


def parse_df(base_path: Path):
    if not base_path.is_dir():
        return None
    result = re.fullmatch(pattern, base_path.name)
    if result is None:
        return None

    id = int(base_path.name.split("_")[-1])
    if id < 100 or id >= 130:
        return None

    setup, index = result.groups()
    csv_file = base_path / "m5out-default-restore" / "lebench_stats.csv"
    if not csv_file.exists():
        return None

    print(base_path.name)

    df = pd.read_csv(csv_file)
    for _, group in df.groupby("name"):
        if len(group) > 1:
            for i, (j, row) in enumerate(group.iterrows()):
                df.loc[j, "name"] += f"-{int(i) + 1}"
    df.insert(0, column="setup", value=setup)
    return df


def main():
    result_dir = proj_dir / "result"
    all_dfs = []
    for base_path in result_dir.iterdir():
        df = parse_df(base_path)
        if df is not None:
            all_dfs.append(df)

    df = pd.concat(all_dfs)

    df2: pd.DataFrame = df.groupby(["setup", "name"]).mean().reset_index()
    df2.to_csv(proj_dir / "scripts" / "plot" / "lebench_stats_all.csv", index=False)


if __name__ == '__main__':
    main()
