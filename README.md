scons build/X86/gem5.fast -j20

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_o3 configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 &> result/baseline_o3/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_o3 configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr &> result/protect_kaslr_o3/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_noncaching configs/example/gem5_library/x86-ubuntu-run-example.py --protect-kaslr


M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_o3_no_panic configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr &> result/protect_kaslr_o3_no_panic/output.log


M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr

M5_OVERRIDE_PY_SOURCE=true /root/gem5/build/X86_MOESI_hammer/gem5.fast --outdir=/root/gem5/result/protect_kaslr_o3_checkpoint /root/gem5/configs/example/gem5_library/gem5-configs/x86-save.py --kaslr-offset=201326592 --load-addr-offset=18446744073525002240 --protect-kaslr --outputs-dir=/root/gem5/result/protect_kaslr_o3_checkpoint --cpu-type=O3 --checkpoint=10000000,10000000000,10 --classic-cache --redirect-stderr --stderr-file=/root/gem5/result/protect_kaslr_o3_checkpoint/output.log --redirect-stdout --stdout-file=/root/gem5/result/protect_kaslr_o3_checkpoint/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.opt configs/example/gem5_library/gem5-configs/x86-save.py --checkpoint=100000000000,10000000000,2 --cpu-type=O3