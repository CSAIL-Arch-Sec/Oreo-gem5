import gzip
from pathlib import Path


script_dir = Path(__file__).resolve().parent
proj_dir = script_dir.parent


def read_file(input_path: Path):
    with gzip.open(input_path, "r") as input_file:
        for line in input_file:
            print(line)
            break


def main():
    read_file(proj_dir / "result/protect_kaslr_module/trace.out.gz")


if __name__ == '__main__':
    main()
