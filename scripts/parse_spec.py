from utils import *
import click
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt
from pprint import pprint

term_str = "term"
val_str = "val"

useful_columns = {
    "simTicks": "simTicks",
    "hostSeconds": "hostSeconds",
    "board.processor.cores.core.numCycles": "numCycles",
    "board.processor.cores.core.idleCycles": "idleCycles",
    # "board.processor.cores.core.quiesceCycles": "quiesceCycles",
    "board.processor.cores.core.commitStats0.numInsts": "numInsts",
    "board.processor.cores.core.commitStats0.numInstsNeedMask": "numInstsNeedMask",
    "board.processor.cores.core.commitStats0.numInstsUser": "numInstsUser",
    "board.processor.cores.core.commitStats0.numMemRefs": "numMemRefs",
    "board.processor.cores.core.commitStats0.numMemRefsNeedMask": "numMemRefsNeedMask",
    "board.processor.cores.core.cpi": "cpi",
    "board.processor.cores.core.ipc": "ipc",
}

default_setup_map = {
    "Baseline": "restore_ko_000_0c0c00",
    "Oreo": "restore_ko_111_0c0c00"
}


def get_useful_columns(core_id_list: list[int] | None):
    if core_id_list is None:
        return useful_columns

    result = {}
    for key, value in useful_columns.items():
        for core_id in core_id_list:
            new_key = re.sub(r"cores", f"cores{core_id}", key)
            result[new_key] = f"{value}{core_id}"
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


def parse_stats_lines(lines: list, core_id_list: list[int] | None, **kwargs):
    core_useful_columns = get_useful_columns(core_id_list)
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
    # if core_id is not None:
    #     df["core-id"] = core_id
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
            x = re.search(r"([\w.]+)-input(\d+)-delta(\d+)_(\d+)", result_dir_name)
            if x is None:
                continue
            benchmark, input_id, delta, ckpt_id = x.groups()
            if benchmark not in benchmark_list:
                continue
            if delta != "32":
                continue
            if int(ckpt_id) not in ckpt_id_list:
                continue
            # Check whether it has some additional output (might imply a error in running)
            board_path = result_dir / "board.pc.com_1.device"
            with board_path.open() as board_file:
                board_last_line = board_file.readlines()[-1].strip()
            # if board_last_line != "Loading new script...":
            if board_last_line == "finish runspec with ret code $?":
                print(f"Warning: {board_path} might encounter an error")
                print(board_last_line)
            # Parse stats file
            stats_path = result_dir / "stats.txt"
            with stats_path.open() as stats_file:
                lines = stats_file.readlines()
            split_lines = split_stats(lines)
            if len(split_lines) > roi_idx:
                lines = split_lines[roi_idx]
                df_list.append(
                    parse_stats_lines(
                        lines=lines, core_id=core_id,
                        name=benchmark, input_id=input_id, ckpt_id=ckpt_id,
                    )
                )
                if len(split_lines) < expected_stats:
                    print(f"Do not have all roi for {stats_path}\n")
            else:
                print(f"Do not have roi for {stats_path}\n")
        df = pd.concat(df_list)
        df["setup"] = setup_name
        setup_df_list.append(df)
    df = pd.concat(setup_df_list)
    df["user ipc"] = df["numInstsUser"].astype(int) / df["numCycles"].astype(int)
    df["user cpi"] = df["numCycles"].astype(int) / df["numInstsUser"].astype(int)
    df.sort_values(["setup", "name", "input_id", "ckpt_id"], inplace=True)
    return df


def get_mean(df: pd.DataFrame, group_by_setup: bool):
    if group_by_setup:
        mean_rows = df.groupby(["setup"]).mean(numeric_only=True).drop(columns="Unnamed: 0")
        mean_rows.reset_index(inplace=True)
    else:
        mean_rows = df.mean(numeric_only=True).drop(columns="Unnamed: 0")
    mean_rows["name"] = "Avg"
    return pd.concat([df, mean_rows])


def cal_mean_overhead(df: pd.DataFrame, group_columns: list, overhead_terms: list):
    mean_df = df.groupby(group_columns).mean()
    mean_df.reset_index(inplace=True)
    # mean_rows = df.groupby(["setup"]).mean(numeric_only=True).drop(columns="Unnamed: 0")
    # mean_rows["name"] = "Avg"
    # mean_rows.reset_index(inplace=True)
    # print(mean_rows)
    # mean_df = pd.concat([mean_df, mean_rows])
    # mean_df.loc[len(mean_df.index)] = mean_df.mean(numeric_only=True)
    # mean_df.loc[len(mean_df.index) - 1, "name"] = "Avg"
    baseline_df = mean_df.loc[mean_df["setup"] == "Baseline"]
    oreo_df = mean_df.loc[mean_df["setup"] == "Oreo"]

    mean_rows = df.groupby(["setup"]).mean(numeric_only=True)
    mean_rows.reset_index(inplace=True)
    mean_rows["name"] = "Avg"
    mean_df = pd.concat([mean_df, mean_rows])
    # print(mean_df)

    index_columns = [ x for x in group_columns if x != "setup" ]
    baseline_df.set_index(index_columns, inplace=True)
    oreo_df.set_index(index_columns, inplace=True)
    overhead_df = pd.DataFrame(index=baseline_df.index)
    for term in overhead_terms:
        overhead_df[term] = (oreo_df[term] - baseline_df[term]) / baseline_df[term] * 100
        overhead_df[f"Baseline {term}"] = baseline_df[term]
        overhead_df[f"Oreo {term}"] = oreo_df[term]
    # print(overhead_df)
    overhead_mean_rows = overhead_df.mean(numeric_only=True)
    overhead_df.loc["Avg"] = overhead_mean_rows
    # print(overhead_df)

    oreo_df["Masked Ratio"] = (oreo_df["numInstsNeedMask"] + oreo_df["numMemRefsNeedMask"]) / (oreo_df["numInsts"] + oreo_df["numMemRefs"]) * 100
    oreo_df.loc["Min"] = oreo_df.min(numeric_only=True)

    return mean_df, overhead_df, oreo_df


def plot_mean(mean_df: pd.DataFrame, overhead_df: pd.DataFrame, y_name: str, output_path: Path):
    plt.figure(figsize=(8, 4))
    sns.set_theme(style="ticks", palette="pastel", font_scale=1)
    ax = sns.barplot(mean_df, x="name", y=y_name, hue="setup", palette=["m", "g"])
    ax.set(xlabel=None, ylabel=f"{(y_name.split()[-1]).upper()}")
    ax.legend(title=None)
    sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
    plt.ylim(0, 2.25)
    print(list(overhead_df[y_name]))
    labels = [f"{x:,.2f}%" for x in list(overhead_df[y_name])]
    print(labels)
    ax.bar_label(ax.containers[1], labels=labels, fontsize=10)
    # for container in ax.containers:
    #     ax.bar_label(container, labels=labels)
    # ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.grid()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_path)


def plot_overhead(overhead_df: pd.DataFrame, y_name: str, output_path: Path):
    plt.figure()
    sns.set_theme(style="ticks", palette="pastel", font_scale=1)
    ax = sns.barplot(overhead_df, x="name", y=y_name)
    ax.set(xlabel=None, ylabel=f"{y_name.upper()} Difference (%)")
    # ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.grid()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_path)


def plot_everything(df: pd.DataFrame, y_name: str, output_dir: Path, suffix: str):
    y_name_no_space = y_name.replace(" ", "_")
    mean_df, overhead_df, oreo_df = cal_mean_overhead(df, ["name", "setup"], [y_name])
    mean_df.to_csv(output_dir / f"merge_input_mean_{y_name_no_space}{suffix}.csv")
    overhead_df.to_csv(output_dir / f"merge_input_overhead_{y_name_no_space}{suffix}.csv", float_format="%.10f")
    oreo_df.to_csv(output_dir / f"merge_input_oreo_{y_name_no_space}{suffix}.csv", float_format="%.10f")
    print(overhead_df.mean(axis=0))
    # y_name = "ipc"
    plot_mean(mean_df, overhead_df, y_name, output_dir / f"merge_input_mean_{y_name_no_space}{suffix}.pdf")
    plot_overhead(overhead_df, y_name, output_dir / f"merge_input_overhead_{y_name_no_space}{suffix}.pdf")


@click.command()
@click.option(
    "--parse-raw",
    is_flag=True,
)
@click.option(
    "--roi-idx",
    type=click.INT,
)
@click.option(
    "--expected-stats",
    type=click.INT,
)
@click.option(
    "--begin-cpt",
    type=click.INT,
    default=0,
)
@click.option(
    "--num-cpt",
    type=click.INT,
    default=0,
)
@click.option(
    "--spec-selector",
    type=click.STRING,
    default="0",
)
def main(
        parse_raw: bool,
        roi_idx: int, expected_stats: int,
        begin_cpt: int, num_cpt: int,
        spec_selector: str,
):
    raw_result_dir = proj_dir / "result"
    output_dir = script_dir / "spec_output"
    output_dir.mkdir(exist_ok=True)

    # benchmark_list = ["401.bzip2"]
    if spec_selector == "0":
        benchmark_list = spec2017_intrate_bench_list
    elif spec_selector == "1":
        benchmark_list = spec2017_intrate_bench_list_first_half
    elif spec_selector == "2":
        benchmark_list = spec2017_intrate_bench_list_second_half
    else:
        benchmark_list = spec2017_intrate_bench_list

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
            # roi_idx=1,
            roi_idx=roi_idx,
            # expected_stats=3,
            expected_stats=expected_stats,
            core_id=None,
            setup_map=default_setup_map,
            benchmark_list=benchmark_list,
            ckpt_id_list=list(range(begin_cpt, begin_cpt + num_cpt))
        )
        df.to_csv(output_dir / f"test_{begin_cpt}_{begin_cpt + num_cpt}_{spec_selector}.csv")
    else:
        spec_selector_list = spec_selector.split("_")
        df_list = []
        for x in spec_selector_list:
            df_list.append(pd.read_csv(output_dir / f"test_{begin_cpt}_{begin_cpt + num_cpt}_{x}.csv"))
        df = pd.concat(df_list)

        if len(spec_selector_list) > 1:
            df.to_csv(output_dir / f"test_{begin_cpt}_{begin_cpt + num_cpt}_0.csv")
            exit(0)
        # df = pd.read_csv(output_dir / f"test_{begin_cpt}_{begin_cpt + num_cpt}.csv")

        # mean_df, overhead_df = cal_mean_overhead(df, ["name", "input_id", "setup"], ["ipc"])
        # mean_df.to_csv(output_dir / f"separate_input_mean_ipc_{begin_cpt}_{begin_cpt + num_cpt}.csv")
        # overhead_df.to_csv(output_dir / f"separate_input_overhead_ipc_{begin_cpt}_{begin_cpt + num_cpt}.csv", float_format="%.10f")
        # print(overhead_df.mean(axis=0))

        plot_everything(df, "ipc", output_dir, f"_{begin_cpt}_{begin_cpt + num_cpt}")
        plot_everything(df, "user ipc", output_dir, f"_{begin_cpt}_{begin_cpt + num_cpt}")
        plot_everything(df, "user cpi", output_dir, f"_{begin_cpt}_{begin_cpt + num_cpt}")

        # mean_df, overhead_df = cal_mean_overhead(df, ["name", "setup"], ["ipc"])
        # mean_df.to_csv(output_dir / f"merge_input_mean_ipc_{begin_cpt}_{begin_cpt + num_cpt}.csv")
        # overhead_df.to_csv(output_dir / f"merge_input_overhead_ipc_{begin_cpt}_{begin_cpt + num_cpt}.csv", float_format="%.10f")
        # print(overhead_df.mean(axis=0))
        # y_name = "ipc"
        # plot_mean(mean_df, overhead_df, y_name, output_dir / f"merge_input_mean_{y_name}_{begin_cpt}_{begin_cpt + num_cpt}.pdf")
        # plot_overhead(overhead_df, y_name, output_dir / f"merge_input_overhead_{y_name}_{begin_cpt}_{begin_cpt + num_cpt}.pdf")

        # mean_df, overhead_df = cal_mean_overhead(df, ["name", "input_id", "setup"], ["cpi"])
        # mean_df.to_csv(output_dir / f"separate_input_mean_cpi_{begin_cpt}_{begin_cpt + num_cpt}.csv")
        # overhead_df.to_csv(output_dir / f"separate_input_overhead_cpi_{begin_cpt}_{begin_cpt + num_cpt}.csv", float_format="%.10f")
        # print(overhead_df.mean(axis=0))
        #
        # mean_df, overhead_df = cal_mean_overhead(df, ["name", "setup"], ["cpi"])
        # mean_df.to_csv(output_dir / f"merge_input_mean_cpi_{begin_cpt}_{begin_cpt + num_cpt}.csv")
        # overhead_df.to_csv(output_dir / f"merge_input_overhead_cpi_{begin_cpt}_{begin_cpt + num_cpt}.csv", float_format="%.10f")
        # print(overhead_df.mean(axis=0))


if __name__ == '__main__':
    main()
