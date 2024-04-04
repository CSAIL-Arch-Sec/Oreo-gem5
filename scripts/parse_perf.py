from utils import *
import click
import pandas as pd


def read_one_setup_result(bench_id_list: list, input_dir: Path):
    result_list = list(map(
        lambda x: pd.read_csv(input_dir / get_lebench_script_name(x) / lebench_result_name),
        bench_id_list))

    df = pd.concat(result_list)
    protect_setup, delta_setup = get_index_from_output_dirname(input_dir.name)
    df["protect_setup"] = protect_setup
    df["delta_setup"] = delta_setup
    df = df.set_index(["protect_setup", "delta_setup", "name"])
    return df


def get_index_from_output_dirname(dirname: str):
    words = dirname.split("_")
    protect_setup = words[2]
    delta_setup = words[3]
    return protect_setup, delta_setup


def read_all_setup_result(bench_id_list: list, setup_dirname_list: list):
    result_dir = proj_dir / "result"
    result_list = list(map(lambda x: read_one_setup_result(bench_id_list, result_dir / x), setup_dirname_list))
    df = pd.concat(result_list)
    return df


def generate_plot_df(df: pd.DataFrame, setup_list: list, plot_col_name: str):
    index_list = list(map(get_index_from_output_dirname, setup_list))
    result_index = pd.MultiIndex.from_tuples(index_list)

    result_list = list(map(lambda x: df.loc[x[0], x[1]][plot_col_name], index_list))
    result = pd.concat(result_list, axis=1).transpose()
    result = result.set_index(result_index)
    print(result)
    return result


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
        "restore_ko_000_000000",
        "restore_ko_000_0c0000",
        "restore_ko_110_0c0000"
    ]
    output_dir = script_dir / "plot"
    output_dir.mkdir(exist_ok=True)
    data_filename = "lebench_new.csv"

    if parse:
        all_data = read_all_setup_result(list(range(len(performance_test_list))), setup_list)
        all_data.to_csv(output_dir / data_filename)
    else:
        all_data = pd.read_csv(output_dir / data_filename, index_col=[0, 1, 2],
                               dtype={"protect_setup": str, "delta_setup": str})

    if plot:
        generate_plot_df(all_data, setup_list, "mean (ns)")
        generate_plot_df(all_data, setup_list, "stddev (ns)")
        generate_plot_df(all_data, setup_list, "closest_k (ns)")


if __name__ == '__main__':
    main()
