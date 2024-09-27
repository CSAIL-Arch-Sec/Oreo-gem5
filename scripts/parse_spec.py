from utils import *
import click
import pandas as pd
import re
from pprint import pprint

term_str = "term"
val_str = "val"

useful_columns = {
    "simTicks": "simTicks",
    "hostSeconds": "hostSeconds",
    "board.processor.cores.core.numCycles": "numCycles",
    "board.processor.cores.core.idleCycles": "idleCycles",
    # "board.processor.cores.core.quiesceCycles": "quiesceCycles",
    "board.processor.cores.core.commitStats0.numInsts": "committedInsts",
    "board.processor.cores.core.cpi": "cpi",
    "board.processor.cores.core.ipc": "ipc",
}

default_setup_map = {
    "Baseline": "restore_ko_000_0c0c00",
    "Oreo": "restore_ko_111_0c0c00"
}


def get_useful_columns(core_id: int | None):
    if core_id is None:
        return useful_columns

    result = {}
    for key, value in useful_columns.items():
        new_key = re.sub(r"core0", f"core{core_id}", key)
        result[new_key] = value
    return result


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


def parse_stats_lines(lines: list, core_id: int | None, **kwargs):
    core_useful_columns = get_useful_columns(core_id)
    data = []
    for line in lines:
        x = parse_stats_line(line)
        if x is not None:
            data.append(x)
    # print("Skip #lines", len(lines) - len(data))
    df = pd.DataFrame(data=data).set_index(0).transpose()
    df.rename(columns=core_useful_columns, inplace=True)
    df = df[core_useful_columns.values()]
    for key, value in kwargs.items():
        df[key] = value
    if core_id is not None:
        df["core-id"] = core_id
    # print(df)
    return df


def parse_all(
        input_dir: Path,
        roi_idx: int, expected_stats: int,
        core_id: int | None,
        setup_map: dict,
        benchmark_list: list,
        ckpt_id_list: list,
):
    setup_df_list = []
    for setup_name, setup_dir_name in setup_map.items():
        df_list = []
        setup_dir = input_dir / setup_dir_name
        for result_dir in setup_dir.iterdir():
            result_dir_name = result_dir.name
            x = re.search(r"([\w.]+)-input(\d+)_(\d+)", result_dir_name)
            if x is None:
                continue
            benchmark, input_id, ckpt_id = x.groups()
            if benchmark not in benchmark_list:
                continue
            if int(ckpt_id) not in ckpt_id_list:
                continue
            # Check whether it has some additional output (might imply a error in running)
            board_path = result_dir / "board.pc.com_1.device"
            with board_path.open() as board_file:
                board_last_line = board_file.readlines()[-1].strip()
            if board_last_line != "Loading new script...":
                print(f"Warning: bench {benchmark} input {input_id} run {ckpt_id} might encounter an error")
            # Parse stats file
            stats_path = result_dir / "stats.txt"
            with stats_path.open() as stats_file:
                lines = stats_file.readlines()
            split_lines = split_stats(lines)
            if len(split_lines) == expected_stats:
                lines = split_lines[roi_idx]
                df_list.append(
                    parse_stats_lines(
                        lines=lines, core_id=core_id,
                        name=benchmark, input_id=input_id, ckpt_id=ckpt_id,
                    )
                )
            else:
                print(f"Do not have enough roi for config {setup_name} benchmark {benchmark} input {input_id} run {ckpt_id}")
        df = pd.concat(df_list)
        df["setup"] = setup_name
        setup_df_list.append(df)
    df = pd.concat(setup_df_list)
    return df


def cal_overhead(df: pd.DataFrame, term_name: str, need_avg: bool):
    if need_avg:
        df[term_name] = (df[f"0.{term_name}"] + df[f"1.{term_name}"]) / 2

    baseline_df = df.loc[df["setup"] == "Baseline"]
    oreo_df = df.loc[df["setup"] == "Oreo"]

    baseline_df.set_index("name", inplace=True)
    oreo_df.set_index("name", inplace=True)
    # print(baseline_df)
    # print(oreo_df)

    cmp_df = pd.DataFrame()
    cmp_df["Baseline"] = baseline_df[term_name]
    cmp_df["Oreo"] = oreo_df[term_name]
    cmp_df = cmp_df[cmp_df[["Baseline", "Oreo"]].notnull().all(1)]
    cmp_df["Overhead"] = (cmp_df["Oreo"] - cmp_df["Baseline"]) / cmp_df["Baseline"]
    print(cmp_df)
    print(cmp_df.mean())


@click.command()
@click.option(
    "--parse-raw",
    is_flag=True,
)
@click.option(
    "--begin-cpt",
    type=click.INT,
)
@click.option(
    "--num-cpt",
    type=click.INT,
)
def main(
        parse_raw: bool,
        begin_cpt: int, num_cpt: int,
):
    raw_result_dir = proj_dir / "result"
    output_dir = script_dir / "spec_output"
    output_dir.mkdir(exist_ok=True)

    # benchmark_list = ["401.bzip2"]
    benchmark_list = spec2017_intrate_bench_list
    benchmark_suffix = "_0"

    # import subprocess
    # server_path = Path("/home/shixins/protect-kaslr/gem5-new/result")
    # for setup_dir_name in default_setup_map.values():
    #     result_path = raw_result_dir / setup_dir_name
    #     for benchmark in spec2006_bench_list:
    #         cmd = f"scp -r shixins@dobby.csail.mit.edu:{server_path / setup_dir_name / f"{benchmark}{benchmark_suffix}"} {result_path}"
    #         print(cmd)
    #         subprocess.run(cmd, shell=True)

    # for setup_dir_name in default_setup_map.values():
    #     for benchmark in spec2006_bench_list:
    #         output_path = raw_result_dir / setup_dir_name / f"{benchmark}{benchmark_suffix}" / "board.pc.com_1.device"
    #         with output_path.open() as output_file:
    #             s = output_file.read()
    #         if re.search("Error loading parse.pl!", s) is not None:
    #             print("Fail", setup_dir_name, benchmark)
    #         else:
    #             print("Success", setup_dir_name, benchmark)

    if parse_raw:
        df = parse_all(
            input_dir=raw_result_dir,
            roi_idx=1,
            expected_stats=3,
            core_id=None,
            setup_map=default_setup_map,
            benchmark_list=benchmark_list,
            ckpt_id_list=list(range(begin_cpt, begin_cpt + num_cpt))
        )
        df.to_csv(output_dir / "test.csv")
    else:
        df = pd.read_csv(output_dir / "test.csv")

        cal_overhead(df, "cpi", True)
        cal_overhead(df, "ipc", True)


if __name__ == '__main__':
    main()
