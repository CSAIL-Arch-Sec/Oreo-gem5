scons build/X86/gem5.fast -j20

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_o3 configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 &> result/baseline_o3/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_o3 configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_noncaching configs/example/gem5_library/x86-ubuntu-run-example.py --protect-kaslr


M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_o3_no_panic configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr &> result/protect_kaslr_o3_no_panic/output.log