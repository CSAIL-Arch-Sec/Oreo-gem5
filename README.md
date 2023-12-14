scons build/X86/gem5.fast -j20

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_o3 configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 &> result/baseline_o3/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_o3 configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr &> result/protect_kaslr_o3/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_noncaching configs/example/gem5_library/x86-ubuntu-run-example.py --protect-kaslr


M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_o3_no_panic configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr &> result/protect_kaslr_o3_no_panic/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr --protect-module-kaslr


M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=o3 --switch-core=o3 --protect-kaslr

M5_OVERRIDE_PY_SOURCE=true /root/gem5/build/X86_MOESI_hammer/gem5.fast --outdir=/root/gem5/result/protect_kaslr_o3_checkpoint /root/gem5/configs/example/gem5_library/gem5-configs/x86-save.py --kaslr-offset=201326592 --load-addr-offset=18446744073525002240 --protect-kaslr --outputs-dir=/root/gem5/result/protect_kaslr_o3_checkpoint --cpu-type=O3 --checkpoint=10000000,10000000000,10 --classic-cache --redirect-stderr --stderr-file=/root/gem5/result/protect_kaslr_o3_checkpoint/output.log --redirect-stdout --stdout-file=/root/gem5/result/protect_kaslr_o3_checkpoint/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.opt configs/example/gem5_library/gem5-configs/x86-save.py --checkpoint=100000000000,10000000000,2 --cpu-type=O3

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=o3 --script=/root/experiments/command-scripts/insmod_test.rcS --protect-module-kaslr &> result/protect_kaslr_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=o3 --script=/root/experiments/command-scripts/module-test/load_unload_hello.rcS --protect-module-kaslr &> result/protect_kaslr_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/protect_kaslr_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=o3 --script=/root/experiments/command-scripts/lkmpg_all.rcS --protect-module-kaslr &> result/protect_kaslr_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=o3 --script=/root/experiments/command-scripts/module-test/load_unload_hello.rcS &> result/baseline_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=o3 --script=/root/experiments/command-scripts/lkmpg_all.rcS &> result/baseline_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=o3 --script=/root/experiments/command-scripts/module-test/quick_test.rcS &> result/baseline_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=result/baseline_module configs/example/gem5_library/x86-ubuntu-run-example.py --starting-core=kvm --switch-core=kvm --script=/root/experiments/command-scripts/lkmpg_all.rcS &> result/baseline_module/output.log

M5_OVERRIDE_PY_SOURCE=true ./build/X86/gem5.fast --outdir=/root/gem5/result/protect_module_anc_0 configs/example/gem5_library/gem5-configs/x86-restore.py --kaslr-offset=201326592 --load-addr-offset=18446744073525002240 --script=/root/gem5/scripts/after_boot/security_test_anc_0 --cpu-type=O3 --redirect-stderr --stderr-file=/root/gem5/result/protect_module_anc_0/output.log --redirect-stdout --stdout-file=/root/gem5/result/protect_module_anc_0/output.log --checkpoint-dir=/root/gem5/result/protect_module_checkpoint_1/default-save/m5out-gen-cpt --outputs-dir=/root/gem5/result/protect_module_anc_0 --protect-module-kaslr

M5_OVERRIDE_PY_SOURCE=true ./build/X86_MOESI_hammer/gem5.fast --outdir=/root/gem5/result/protect_module_anc_0 configs/example/gem5_library/gem5-configs/x86-restore.py --kaslr-offset=201326592 --load-addr-offset=18446744073525002240 --script=/root/gem5/scripts/after_boot/security_test_anc_0 --cpu-type=O3 --redirect-stderr --stderr-file=/root/gem5/result/protect_module_anc_0/output.log --redirect-stdout --stdout-file=/root/gem5/result/protect_module_anc_0/output.log --checkpoint-dir=/root/gem5/result/protect_module_checkpoint_1/default-save/m5out-gen-cpt --outputs-dir=/root/gem5/result/protect_module_anc_0 --protect-module-kaslr
