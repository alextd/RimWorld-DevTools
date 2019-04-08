#Runs a 'Release' build of ModFolder/*.sln
# releaseZip.py ModFolder
#Assuming you use the RimWorld cookie cutter
#(which creates a release folder 'Mod - Release')
#This script also zips it up.

import os
import sys
import shutil


def doRelease(dir):
	if not os.path.isdir(dir):
		print(f"'{dir}' is not a directory")
		sys.exit(0)
		
	for path in os.listdir(dir):
		if path.endswith(".sln"):
			print(path)
			os.system("MsBuild.exe \"" + os.path.join(dir, path) + "\" /t:Build /p:Configuration=Release /verbosity:minimal")


def doZip(dir):
	for releaseDir in os.listdir("."):
		if releaseDir.replace(" ","").startswith(dir) and releaseDir.endswith(" - Release"):
			zipFile = releaseDir
			print(f"Zipping {releaseDir}")
			shutil.make_archive(zipFile, 'zip', ".", releaseDir)
		
if len(sys.argv) == 1:
	print("need dir as argv")
	sys.exit(0)

doRelease(sys.argv[1])
doZip(sys.argv[1])