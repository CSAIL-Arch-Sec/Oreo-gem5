from utils import *
from pathlib import Path
import click
import multiprocessing


def switch_simple(
        starting_core: str, swith_core: str,
        protect_args: str,
        delta_args: str,
        use_uuid: bool,
        exp_script_path: Path
):
    protect_arg_dict = gen_protect_args(protect_args)
    delta_arg_dict = gen_delta_args(delta_args)

    ret, output_dir = run_one_test(
        sim_mode=SimMode.SIMPLE,
        sim_option="fast", debug_flags="",
        starting_core=starting_core, switch_core=swith_core,
        sim_cpu_cores=1,
        exp_script_path=exp_script_path,
        add_checkpoint="",
        use_uuid=use_uuid,
        uuid_str="",
        suffix="",
        **protect_arg_dict,
        **delta_arg_dict,
    )

    if ret:
        print(f"Failed run with switch core {starting_core}->{swith_core}, ret = {ret}!!!")
        return None
    else:
        print(f"Successfully generating one checkpoint with switch core {starting_core}->{swith_core}.")
        return output_dir


def main():
    # script = (f"m5 exit\n"
    #           f"cd /home/gem5/experiments/modules\n"
    #           f"insmod set_protection.ko module_delta=12 user_delta=0\n"
    #           f"lsmod\n"
    #           f"dmesg | tail -n300\n"
    #           f"sleep 100")

    user_delta = 1
    size = "test"
    # bench_name = "502.gcc_r"
    # bench_name = "500.perlbench_r"
    bench_name = "557.xz_r.2"

    # script = (
    #     f"cd /home/gem5/spec2017\n"
    #     f"source shrc\n"
    #     f"sleep 1\n"
    #     f"m5 exit\n"
    #     # f"m5 resetstats\n"
    #     f"runcpu --size {size} --iterations 1 --config myconfig.x86.cfg --define gcc_dir=\"/usr\" --noreportable --nobuild {bench_name}\n"
    #     # f"echo 'finish runspec with ret code $?'\n"
    #     f"m5 dumpresetstats\n"
    #     f"sleep 1\n"
    #     f"m5 exit\n"
    # )

    script = (
        # f"sleep 1\n"
        # f"m5 exit\n"
        # f"cd /home/gem5/experiments/modules\n"
        # f"insmod set_protection.ko user_delta={user_delta}\n"
        # f"cd /home/gem5/spec2017/benchspec/CPU/502.gcc_r/run/run_base_test_mytest-m64.0000\n"
        # f"cd /home/gem5/spec2017/benchspec/CPU/500.perlbench_r/run/run_base_test_mytest-m64.0000\n"
        # f"cd /home/gem5/spec2017/benchspec/CPU/525.x264_r/run/run_base_refrate_mytest-m64.0000\n"
        f"cd /home/gem5/spec2017/benchspec/CPU/557.xz_r/run/run_base_refrate_mytest-m64.0000\n"
        f"sleep 1\n"
        f"m5 exit\n"
        # f"m5 resetstats\n"
        # f"./cpugcc_r_base.mytest-m64 t1.c -O3 -finline-limit=50000 -o t1.opts-O3_-finline-limit_50000.s\n"
        # f"./cpugcc_r_base.mytest-m64 t1.c -O3 -o t1.opts-O3_-finline-limit_50000.s\n"
        # f"./perlbench_r_base.mytest-m64 -I. -I./lib test.pl\n"
        # f"../run_base_refrate_mytest-m64.0000/x264_r_base.mytest-m64 --pass 2 --stats x264_stats.log --bitrate 1000 --dumpyuv 200 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720\n"
        # f"../run_base_refrate_mytest-m64.0000/xz_r_base.mytest-m64 cpu2006docs.tar.xz 250 055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae 23047774 23513385 6e\n"
        f"../run_base_refrate_mytest-m64.0000/xz_r_base.mytest-m64 smalltest.tar.xz 1 f4f0c954053151bab29bd2283f49edced311239a4b5959f93f15ed647ba5482d79323b63d71616f10f7a9bfd6520b7736093a7f00635e427ac14ccfb7cc887e7 23047774 23513385 6e\n"
        f"m5 dumpresetstats\n"
        f"sleep 1\n"
        f"m5 exit\n"
    )

    output_dir = script_dir / "other_scripts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"spec2017-{bench_name}.rcS"
    with output_path.open(mode="w") as output_file:
        output_file.write(script)

    args_list = [
        # ["kvm", "kvm", "0,0,0", "0,0,0", False, output_path],
        ["kvm", "o3", "0,0,0", "0,0,0", False, output_path],
    ]

    with multiprocessing.Pool(16) as p:
        p.starmap(switch_simple, args_list)


if __name__ == '__main__':
    main()
