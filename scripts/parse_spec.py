from utils import *
import click
import pandas as pd
import re

term_str = "term"
val_str = "val"

useful_columns = {
    "simTicks": "simTicks",
    "hostSeconds": "hostSeconds",
    "board.processor.cores0.core.numCycles": "0.numCycles",
    "board.processor.cores0.core.idleCycles": "0.idleCycles",
    "board.processor.cores0.core.quiesceCycles": "0.quiesceCycles",
    "board.processor.cores0.core.committedInsts": "0.committedInsts",
    "board.processor.cores0.core.cpi": "0.cpi",
    "board.processor.cores1.core.numCycles": "1.numCycles",
    "board.processor.cores1.core.idleCycles": "1.idleCycles",
    "board.processor.cores1.core.quiesceCycles": "1.quiesceCycles",
    "board.processor.cores1.core.committedInsts": "1.committedInsts",
    "board.processor.cores1.core.cpi": "1.cpi ",
}

default_setup_map = {
    "Baseline": "restore_ko_000_0c0c00",
    "Oreo": "restore_ko_111_0c0c00"
}

def split_stats(lines: list):
    start_lines = []
    end_lines = []
    for i, line in enumerate(lines):
        if re.search(r"---------- Begin Simulation Statistics ----------", line) is not None:
            start_lines.append(i)
            assert len(start_lines) == len(end_lines) + 1
        if re.search(r"---------- End Simulation Statistics   ----------", line) is not None:
            end_lines.append(i)
            assert len(start_lines) == len(end_lines)
    result = []
    for k in range(len(start_lines)):
        result.append(lines[(start_lines[k]+1):end_lines[k]])
    return result


def parse_stats_line(line: str):
    no_comment_line = line.split("#")[0].strip()
    words = no_comment_line.split()
    if len(words) == 2:
        # return [words[0], float(words[1])]
        return words
    else:
        # print("Skip line")
        # print(line)
        return None


def parse_stats_lines(lines: list, name: str):
    data = []
    for line in lines:
        x = parse_stats_line(line)
        if x is not None:
            data.append(x)
    print("Skip #lines", len(lines) - len(data))
    df = pd.DataFrame(data=data).set_index(0).transpose()
    df.rename(columns=useful_columns, inplace=True)
    df = df[useful_columns.values()]
    df["name"] = name
    print(df)
    return df


def parse_all(input_dir: Path, roi_idx: int, setup_map: dict, benchmark_list: list, benchmark_suffix: str):
    setup_df_list = []
    for setup_name, setup_dir_name in setup_map.items():
        df_list = []
        for benchmark in benchmark_list:
            stats_path = input_dir / setup_dir_name / f"{benchmark}{benchmark_suffix}" / "stats.txt"
            with stats_path.open() as stats_file:
                lines = stats_file.readlines()
            lines = split_stats(lines)[roi_idx]
            df_list.append(parse_stats_lines(lines, benchmark))
        df = pd.concat(df_list)
        df["setup"] = setup_name
        setup_df_list.append(df)
    df = pd.concat(setup_df_list)
    return df


def main():
    raw_result_dir = proj_dir / "result"
    output_dir = script_dir / "spec_output"
    output_dir.mkdir(exist_ok=True)

    # benchmark_list = ["401.bzip2"]
    benchmark_list = spec_bench_list
    benchmark_suffix = "_0"

    df = parse_all(
        input_dir=raw_result_dir,
        roi_idx=1,
        setup_map=default_setup_map,
        benchmark_list=benchmark_list,
        benchmark_suffix=benchmark_suffix
    )
    df.to_csv(output_dir / "test.csv")


if __name__ == '__main__':
    main()
