-E DBUS_SESSION_BUS_ADDRESS 'unix:path=/run/user/1000/bus'
-E DISPLAY localhost:10.0
-E HOME /home/gem5
-E LANG en_US.UTF-8
-E LC_ALL C
-E LC_LANG C
-E LD_LIBRARY_PATH /usr/lib64/:/usr/lib/:/lib64
-E LESSCLOSE '/usr/bin/lesspipe %s %s'
-E LESSOPEN '| /usr/bin/lesspipe %s'
-E LIBC_FATAL_STDERR_ 1
-E LOGNAME gem5
-E LS_COLORS 'rs=0:di=01;34:ln=01;36:mh=00:pi=40;33:so=01;35:do=01;35:bd=40;33;01:cd=40;33;01:or=40;31;01:mi=00:su=37;41:sg=30;43:ca=30;41:tw=30;42:ow=34;42:st=37;44:ex=01;32:*.tar=01;31:*.tgz=01;31:*.arc=01;31:*.arj=01;31:*.taz=01;31:*.lha=01;31:*.lz4=01;31:*.lzh=01;31:*.lzma=01;31:*.tlz=01;31:*.txz=01;31:*.tzo=01;31:*.t7z=01;31:*.zip=01;31:*.z=01;31:*.dz=01;31:*.gz=01;31:*.lrz=01;31:*.lz=01;31:*.lzo=01;31:*.xz=01;31:*.zst=01;31:*.tzst=01;31:*.bz2=01;31:*.bz=01;31:*.tbz=01;31:*.tbz2=01;31:*.tz=01;31:*.deb=01;31:*.rpm=01;31:*.jar=01;31:*.war=01;31:*.ear=01;31:*.sar=01;31:*.rar=01;31:*.alz=01;31:*.ace=01;31:*.zoo=01;31:*.cpio=01;31:*.7z=01;31:*.rz=01;31:*.cab=01;31:*.wim=01;31:*.swm=01;31:*.dwm=01;31:*.esd=01;31:*.jpg=01;35:*.jpeg=01;35:*.mjpg=01;35:*.mjpeg=01;35:*.gif=01;35:*.bmp=01;35:*.pbm=01;35:*.pgm=01;35:*.ppm=01;35:*.tga=01;35:*.xbm=01;35:*.xpm=01;35:*.tif=01;35:*.tiff=01;35:*.png=01;35:*.svg=01;35:*.svgz=01;35:*.mng=01;35:*.pcx=01;35:*.mov=01;35:*.mpg=01;35:*.mpeg=01;35:*.m2v=01;35:*.mkv=01;35:*.webm=01;35:*.webp=01;35:*.ogm=01;35:*.mp4=01;35:*.m4v=01;35:*.mp4v=01;35:*.vob=01;35:*.qt=01;35:*.nuv=01;35:*.wmv=01;35:*.asf=01;35:*.rm=01;35:*.rmvb=01;35:*.flc=01;35:*.avi=01;35:*.fli=01;35:*.flv=01;35:*.gl=01;35:*.dl=01;35:*.xcf=01;35:*.xwd=01;35:*.yuv=01;35:*.cgm=01;35:*.emf=01;35:*.ogv=01;35:*.ogx=01;35:*.aac=00;36:*.au=00;36:*.flac=00;36:*.m4a=00;36:*.mid=00;36:*.midi=00;36:*.mka=00;36:*.mp3=00;36:*.mpc=00;36:*.ogg=00;36:*.ra=00;36:*.wav=00;36:*.oga=00;36:*.opus=00;36:*.spx=00;36:*.xspf=00;36:'
-E MOTD_SHOWN pam
-E OLDPWD /home/gem5
-E OMP_NUM_THREADS 1
-E OMP_THREAD_LIMIT 1
-E PATH /home/gem5/spec2017/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
-E SHELL /bin/bash
-E SPEC /home/gem5/spec2017
-E SPECDB_PWD /home/gem5/spec2017
-E SPECPERLLIB /home/gem5/spec2017/bin/lib:/home/gem5/spec2017/bin
-E SSH_CLIENT '172.16.65.1 56668 22'
-E SSH_CONNECTION '172.16.65.1 56668 172.16.65.128 22'
-E SSH_TTY /dev/pts/0
-E TERM xterm-256color
-E USER gem5
-E XDG_DATA_DIRS /usr/local/share:/usr/share:/var/lib/snapd/desktop
-E XDG_RUNTIME_DIR /run/user/1000
-E XDG_SESSION_CLASS user
-E XDG_SESSION_ID 3
-E XDG_SESSION_TYPE tty
-r
-N C
-C /home/gem5/spec2017/benchspec/CPU/557.xz_r/run/run_base_refrate_mytest-m64.0000
-o cld.tar-160-6.out -e cld.tar-160-6.err ../run_base_refrate_mytest-m64.0000/xz_r_base.mytest-m64 cld.tar.xz 160 19cf30ae51eddcbefda78dd06014b4b96281456e078ca7c13e1c0c9e6aaea8dff3efb4ad6b0456697718cede6bd5454852652806a657bb56e07d61128434b474 59796407 61004416 6 > cld.tar-160-6.out 2>> cld.tar-160-6.err
-o cpu2006docs.tar-250-6e.out -e cpu2006docs.tar-250-6e.err ../run_base_refrate_mytest-m64.0000/xz_r_base.mytest-m64 cpu2006docs.tar.xz 250 055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae 23047774 23513385 6e > cpu2006docs.tar-250-6e.out 2>> cpu2006docs.tar-250-6e.err
-o input.combined-250-7.out -e input.combined-250-7.err ../run_base_refrate_mytest-m64.0000/xz_r_base.mytest-m64 input.combined.xz 250 a841f68f38572a49d86226b7ff5baeb31bd19dc637a922a972b2e6d1257a890f6a544ecab967c313e370478c74f760eb229d4eef8a8d2836d233d3e9dd1430bf 40401484 41217675 7 > input.combined-250-7.out 2>> input.combined-250-7.err
