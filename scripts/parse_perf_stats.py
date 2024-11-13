from parse_spec import *
from utils import *


def parse_all_perf(
        input_dir: Path,
        roi_idx: int, expected_stats: int,
        core_id_list: list[int] | None,
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
            x = re.search(r"([\w.]+)_(\d+)", result_dir_name)
            if x is None:
                continue
            benchmark, ckpt_id = x.groups()
            if benchmark not in benchmark_list:
                continue
            if int(ckpt_id) not in ckpt_id_list:
                continue
            print(benchmark, ckpt_id)
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
                        lines=lines, core_id_list=core_id_list,
                        name=benchmark, ckpt_id=ckpt_id,
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
    # df["user ipc"] = df["numInstsUser"].astype(int) / df["numCycles"].astype(int)
    # df["user cpi"] = df["numCycles"].astype(int) / df["numInstsUser"].astype(int)
    df.sort_values(["setup", "name", "ckpt_id"], inplace=True)
    return df


@click.command()
@click.option(
    "--parse-raw",
    is_flag=True,
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
def main(parse_raw: bool, begin_cpt: int, num_cpt: int,):
    raw_result_dir = proj_dir / "result"
    output_dir = script_dir / "lebench_output"
    output_dir.mkdir(exist_ok=True)

    benchmark_list = [ f"lebench_{x}" for x in range(len(performance_test_list)) ]
    print(benchmark_list)

    setup_map = {
        "Oreo": "restore_ko_111_0c0c00"
    }

    if parse_raw:
        df = parse_all_perf(
            input_dir=raw_result_dir,
            roi_idx=1,
            expected_stats=2,
            core_id_list=[0, 1],
            setup_map=setup_map,
            benchmark_list=benchmark_list,
            ckpt_id_list=list(range(begin_cpt, begin_cpt + num_cpt))
        )

        df.to_csv(output_dir / "test.csv")
    else:
        df = pd.read_csv(output_dir / "test.csv")

    df["Masked Ratio"] = ((df["numInstsNeedMask0"] + df["numInstsNeedMask1"] + df["numMemRefsNeedMask0"] + df["numMemRefsNeedMask1"]) /
                          (df["numInsts0"] + df["numInsts1"] + df["numMemRefs0"] + df["numMemRefs1"]) * 100)
    df.loc["Min"] = df.min(numeric_only=True)
    df.loc["Max"] = df.max(numeric_only=True)
    df.loc["Avg"] = df.mean(numeric_only=True)
    df.to_csv(output_dir / "test_mask_ratio.csv")


if __name__ == '__main__':
    main()
