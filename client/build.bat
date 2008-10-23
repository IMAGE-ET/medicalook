set PIP=c:\python25\pyInstaller\
python %PIP%Makespec.py --onefile --noconsole --upx --icon=images\medicalook.ico medicalook.py
python %PIP%Build.py medicalook.spec