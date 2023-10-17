import click
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import rc
from pathlib import Path
from utils import *

font = {'family' : 'serif',
        'serif': ['Times'],
        # 'weight' : 'bold',
        'size': 12}
rc('font',**font)
rc('text', usetex=True)


def parse_one_file(
        protect_mode: list,
        bench_id: int,
):
    result_path = proj_dir / "result" / f"{get_mode_name(*protect_mode)}_lebench_{bench_id}" / \
                  "m5out-default-restore" / "lebench_stats.csv"

    if not result_path.exists():
        return None

    df = pd.read_csv(result_path)
    df["Setup"] = get_col_name(*protect_mode)
    # if len(df) > 0:
    #     for i in range(len(df)):
    #         df.iloc[i]["name"] = f"{df.iloc[i]['name']}_{i}"
    df = df.set_index(["Setup", "name"])
    return df


def parse_all_files(mode_list: list, bench_list: list):
    df_list = []
    for protect_mode in mode_list:
        for bench_id in bench_list:
            x = parse_one_file(protect_mode, bench_id)
            if x is None:
                continue
            else:
                df_list.append(x)

    df = pd.concat(df_list)
    print(df)
    return df


@click.command()
@click.option(
    "--parse-data",
    is_flag=True
)
@click.option(
    "--plot-result",
    is_flag=True
)
@click.option(
    "--config-str",
    type=click.STRING
)
@click.option(
    "--run-list",
    type=click.STRING,
    default=""
)
@click.option(
    "--file-name",
    type=click.STRING,
    default="lebench"
)
@click.option(
    "--measure-term",
    type=click.STRING,
)
@click.option(
    "--measure-unit",
    type=click.STRING,
)
def main(parse_data: bool, plot_result: bool, 
         config_str: str, run_list: str, file_name: str,
         measure_term: str, measure_unit):
    plot_dir = proj_dir / "scripts" / "plot"
    plot_dir.mkdir(exist_ok=True)

    if parse_data:
        all_mode_list = [
            [False, False],
            [False, True],
            [True, False],
            [True, True]
        ]
        if run_list == "":
            bench_list = list(range(len(performance_test_list)))
        else:
            bench_list = list(map(lambda x: int(x), run_list.split(",")))

        print(config_str)
        config_options = config_str.split(",")
        mode_list = []
        for config in config_options:
            mode_list.append(all_mode_list[int(config)])

        df = parse_all_files(mode_list, bench_list)
        df.to_csv(plot_dir / f"{file_name}.csv")
    else:
        df = pd.read_csv(plot_dir / f"{file_name}.csv", index_col=[0, 1])

    if plot_result:
        # print(df)
        # err_df = pd.DataFrame()
        # i = 0
        # for group_name, _ in df.groupby(level=0):
        #     setup_df = df.loc[group_name][f"stddev ({measure_unit})"].reset_index()
        #     setup_df = setup_df.rename(columns={f"stddev ({measure_unit})": group_name})
        #     setup_df = setup_df.drop("name", axis=1)
        #     if i == 0:
        #         err_df = setup_df
        #         i += 1
        #     else:
        #         err_df = err_df.merge(setup_df, left_index=True, right_index=True)
        # print(err_df)
        plt.figure()
        measure_name = f"{measure_term} ({measure_unit})"
        ax = sns.barplot(x="name", y=measure_name, hue="Setup", data=df)
        # ax = sns.barplot(x="name", y=measure_name, hue="setup", data=df)
        plt.xticks(rotation=90)
        plt.tight_layout()
        # plt.show()
        plt.savefig(plot_dir / f"{file_name}_{measure_term}.pdf")

        baseline = df.loc["Baseline"]
        oreo = df.loc["Oreo"]
        # baseline = df.loc["none"]
        # oreo = df.loc["both"]
        result = ((oreo[measure_name] / baseline[measure_name]) - 1) * 100

        overhead_df = pd.DataFrame(result)
        print(overhead_df.sort_index())
        print(overhead_df.mean())
        print(f"{(overhead_df.gt(-1) & overhead_df.lt(1)).sum()['closest_k (ns)']}/{len(overhead_df)} benches have overhead < 1%")
        print(f"{(overhead_df.gt(-2) & overhead_df.lt(2)).sum()['closest_k (ns)']}/{len(overhead_df)} benches have overhead < 2%")
        print(f"{(overhead_df.gt(-3) & overhead_df.lt(3)).sum()['closest_k (ns)']}/{len(overhead_df)} benches have overhead < 3%")
        # print(f"{overhead_df[overhead_df < 2].count()['closest_k (ns)']}/{len(overhead_df)} benches have overhead < 2%")
        # print(overhead_df[overhead_df < 1].count())

        plt.figure(figsize=(6, 3))
        ax = sns.barplot(x="name", y=measure_name, data=overhead_df, zorder=3)
        ax.set(xlabel="", ylabel="Overhead (\%)")
        ax.grid(axis='x', which='both', alpha=0.5, zorder=0)
        plt.xticks(rotation=60, ha="right", va="top", rotation_mode="anchor")
        plt.tight_layout()
        # plt.show()
        plt.savefig(plot_dir / f"{file_name}_{measure_term}_overhead.pdf")



if __name__ == '__main__':
    main()
