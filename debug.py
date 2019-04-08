#Runs a 'Debug' build of ModFolder/*.sln
# debug.py ModFolder
import os
import sys
import shutil


def doDebug(dir):
	if not os.path.isdir(dir):
		print(f"'{dir}' is not a directory")
		sys.exit(0)
		
	for path in os.listdir(dir):
		if path.endswith(".sln"):
			print(path)
			os.system("MsBuild.exe \"" + os.path.join(dir, path) + "\" /t:Build /p:Configuration=Debug /verbosity:minimal")

		
if len(sys.argv) == 1:
	print("need dir as argv")
	sys.exit(0)

doDebug(sys.argv[1])