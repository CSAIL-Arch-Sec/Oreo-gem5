../run_base_refrate_mytest-m64.0000/x264_r_base.mytest-m64 --pass 1 --stats x264_stats.log --bitrate 1000 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720
../run_base_refrate_mytest-m64.0000/x264_r_base.mytest-m64 --pass 2 --stats x264_stats.log --bitrate 1000 --dumpyuv 200 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720
../run_base_refrate_mytest-m64.0000/x264_r_base.mytest-m64 --seek 500 --dumpyuv 200 --frames 1250 -o BuckBunny_New.264 BuckBunny.yuv 1280x720
