from utils import *
import click
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from strenum import StrEnum


class ColName(StrEnum):
    name = "name"
    protect_setup = "protect_setup"
    delta_setup = "delta_setup"
    bench_id = "bench_id"
    iteration = "iter"
    closest_k = "closest_k (ns)"
    mean = "mean (ns)"
    setup = "setup"


class ColNamePrefix(StrEnum):
    mean = "mean"
    median = "median"
    normalize_mean = "normalize mean"
    normalize_median = "normalize median"


def add_prefix_col_name(col: str, prefix: ColNamePrefix):
    return f"{prefix} {col}"


def read_one_setup_result(bench_id_list: list, input_dir: Path, suffix_list: list):
    df_list = []
    for bench_id in bench_id_list:
        for suffix in suffix_list:
            if suffix is not None:
                suffix_str = f"_{suffix}"
            else:
                suffix_str = ""
            csv_path = input_dir / f"{get_lebench_script_name(bench_id)}{suffix_str}" / lebench_result_name
            if not csv_path.exists():
                # print(csv_path, "does not exist")
                continue
            one_df = pd.read_csv(csv_path)
            if len(one_df.index) > 1:
                assert len(one_df.index == 2)
                one_df.loc[0, ColName.name] = one_df.loc[0, ColName.name] + "-parent"
                one_df.loc[1, ColName.name] = one_df.loc[1, ColName.name] + "-child"
            one_df[ColName.iteration] = suffix
            one_df[ColName.bench_id] = bench_id
            df_list.append(one_df)

    df = pd.concat(df_list)
    protect_setup, delta_setup = get_index_from_output_dirname(input_dir.name)
    df[ColName.protect_setup] = protect_setup
    df[ColName.delta_setup] = delta_setup
    df = df.set_index([ColName.protect_setup, ColName.delta_setup, ColName.bench_id, ColName.name, ColName.iteration])
    return df


def get_index_from_output_dirname(dirname: str):
    words = dirname.split("_")
    protect_setup = words[2]
    delta_setup = words[3]
    return protect_setup, delta_setup


def read_all_setup_result(bench_id_list: list, setup_dirname_list: list, suffix_list: list):
    result_dir = proj_dir / "result"
    result_list = list(map(lambda x: read_one_setup_result(bench_id_list, result_dir / x, suffix_list), setup_dirname_list))
    df = pd.concat(result_list)
    return df


def normalize_df(df: pd.DataFrame):
    mean_df = df.groupby([ColName.bench_id, ColName.name]).mean()
    mean_df = mean_df.rename(lambda x: add_prefix_col_name(x, ColNamePrefix.mean), axis="columns")
    median_df = df.groupby([ColName.bench_id, ColName.name]).median()
    median_df = median_df.rename(lambda x: add_prefix_col_name(x, ColNamePrefix.median), axis="columns")
    orig_cols = df.columns
    df = df.join(mean_df, on=[ColName.bench_id, ColName.name])
    df = df.join(median_df, on=[ColName.bench_id, ColName.name])
    print(df)
    for col in orig_cols:
        df[add_prefix_col_name(col, ColNamePrefix.normalize_mean)] = df[col] / df[add_prefix_col_name(col, ColNamePrefix.mean)]
        df[add_prefix_col_name(col, ColNamePrefix.normalize_median)] = df[col] / df[add_prefix_col_name(col, ColNamePrefix.median)]
    return df


def generate_plot_df(df: pd.DataFrame, setup_list: list, plot_col_name: str):
    index_list = list(map(get_index_from_output_dirname, setup_list))
    result_index = pd.MultiIndex.from_tuples(index_list)

    result_list = list(map(lambda x: df.loc[x[0], x[1]][plot_col_name], index_list))
    result = pd.concat(result_list, axis=1).transpose()
    result = result.set_index(result_index)
    print(result)
    return result


def get_plot_name(col_name: ColName, col_name_prefix: ColNamePrefix):
    col_name_no_space = col_name.split()[0]
    col_name_prefix_no_space = col_name_prefix.replace(" ", "_")
    return f"lebench_{col_name_no_space}_{col_name_prefix_no_space}.pdf"


def generate_plot(data: pd.DataFrame, output_dir: Path, col_name: ColName, col_name_prefix: ColNamePrefix):
    plt.figure(figsize=(16, 9))
    sns.set_theme(style="ticks", palette="pastel", font_scale=1.5)
    ax = sns.boxplot(x=ColName.name, y=add_prefix_col_name(col_name, col_name_prefix),
                hue=ColName.setup, palette=["m", "g"],
                data=data,
                width=0.5)
    # sns.despine(offset=10, trim=True)
    ax.axhline(y=1, linewidth=1, color='gray', ls='-')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_dir / get_plot_name(col_name, col_name_prefix))


@click.command()
@click.option(
    "--parse",
    is_flag=True,
)
@click.option(
    "--plot",
    is_flag=True,
)
def main(parse: bool, plot: bool):
    setup_list = [
        # "restore_ko_000_000000",
        "restore_ko_000_0c0c00",
        "restore_ko_111_0c0c00"
    ]
    output_dir = script_dir / "plot"
    output_dir.mkdir(exist_ok=True)
    data_filename = "lebench_new.csv"

    suffix_list = list(range(6))

    if parse:
        all_data = read_all_setup_result(list(range(len(performance_test_list))), setup_list, suffix_list)
        all_data = normalize_df(all_data)
        all_data.reset_index(level=[ColName.protect_setup, ColName.delta_setup, ColName.bench_id, ColName.name, ColName.iteration],
                             inplace=True)
        all_data[ColName.setup] = all_data[ColName.protect_setup].apply(lambda x: "Baseline" if x == "000" else "Oreo")
        all_data.to_csv(output_dir / data_filename)
    else:
        all_data = pd.read_csv(output_dir / data_filename, index_col=0,
                               dtype={ColName.protect_setup: str, ColName.delta_setup: str})

    if plot:
        # generate_plot_df(all_data, setup_list, "mean (ns)")
        # generate_plot_df(all_data, setup_list, "stddev (ns)")
        # generate_plot_df(all_data, setup_list, "closest_k (ns)")

        generate_plot(all_data, output_dir, ColName.closest_k, ColNamePrefix.normalize_mean)
        generate_plot(all_data, output_dir, ColName.closest_k, ColNamePrefix.normalize_median)
        generate_plot(all_data, output_dir, ColName.mean, ColNamePrefix.normalize_mean)
        generate_plot(all_data, output_dir, ColName.mean, ColNamePrefix.normalize_median)

    # plt.figure(figsize=(16, 9))
    # sns.set_theme(style="ticks", palette="pastel", font_scale=1.5)
    # sns.boxplot(x=ColName.name, y=get_normalize_col_name(ColName.closest_k),
    #             hue=ColName.protect_setup, palette=["m", "g"],
    #             data=all_data,
    #             width=0.5)
    # sns.despine(offset=10, trim=True)
    # plt.xticks(rotation=90)
    # plt.tight_layout()
    # plt.savefig(output_dir / "lebench_new.pdf")


if __name__ == '__main__':
    main()
