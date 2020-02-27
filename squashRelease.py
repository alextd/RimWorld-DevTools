# RimWorld mod 1.1/1.0 support.
# Build your 1.1 mod as if it only supported 1.1
# Keep an old 1.0 mod release as a base.
# Then use this tool to make the release version for 1.1/1.0
#
# The basic target structure is for all 1.0 files to go in the root Mod/
# Any new or changed content ends up in Mod/1.1
#  (And in the future , 1.2 as well?)
#
#  python squashRelease.py Version ModNew ModOld
#  (python3 of course)
#
# This tool squashes a 1.1-only NewMod folder and a 1.0 OldMod folder to make a dual-version NewMod folder.
# Unchanged files are kept in NewMod/
# New files are put in NewMod/1.1/
# Changed files also go in NewMod/1.1/
# - The old 1.0 versions are coped in from OldMod/ to NewMod/
# The resulting NewMod folder should have a suitable release for 1.1/1.0 with no duplicate copies.
#
# The entire About/ folder is simply taken from 1.1 and 1.0 is ignored.
# (But this does grab PublishedFileId.txt from 1.0 so 1.1 can be updated on Steam)
# Note: The About.xml is not edited, so it should just lie and include 1.1 and 1.0,
#  even though it only does 1.1 originally
#
# TODO: 1.2 and above, using LoadFolders.xml to include 1.2 -> 1.1 -> /
#  (if your mod needs 1.1 to remove a file that 1.0 had, then you can't use this script
#   since the existence of the 1.0 file would make 1.1 use it - your own LoadFolders.xml can handle that)
#
## --------------
#
#  HOW TO:
# Step 1: Keep a static, unchanging copy of the 1.0 release in ModOld
# Step 2: Build 1.1 version in ModNew ready for release, with no 1.0 support
# Step 3: Squash them together - now the ModNew folder supports 1.1 and 1.0
#
# Future 1.1 mod updates should be done with a fresh 1.1 build squashed onto the original 1.0
# (i.e. delete ModNew and re-build)

# Doesn't handle:
# Added translation lines. That could just be added to the base folder.
# It would be tricky to tell if it's just a newline and not a changed line.
# So 1.1 will get a copy of translations.

import os
import sys
import shutil
from pathlib import PurePath
import filecmp

def fuckinMakeTheDirectoryOkay(outfilename):
	try:
		os.makedirs(os.path.dirname(outfilename))
	except:
		pass

		
def doSquash(ver, new, old):
	print(f"\n-Squashing {new}({ver}) onto {old}")
	#walk the new folder, find new files or changed files
	
	#Let's not squash twice. It needs clean and rebuild
	verDir = os.path.join(new, ver)
	if os.path.exists(verDir):
		print(f"--  !Nope! Already Squashed it.")
		return
	print(f"  --  New changes going into {verDir}")
	
	#Ah gee. First thing, get the PublishedFileId.txt
	shutil.copy2(os.path.join(old, "About/PublishedFileId.txt"), os.path.join(new, "About/PublishedFileId.txt"))
		
	for dname, dirs, files in os.walk(new):
		#Ignore /About
		print(f" - {dname}")
		if not dname.endswith("About"):
			#Find the relative path inside the mod folder
			relpath = str(PurePath(dname).relative_to(new))
			
			for fname in files:
				newPath = os.path.join(dname, fname)
				oldPath = os.path.join(old, relpath, fname)
				
				#todo 1.2 onto 1.1 midpath
				
				print(f"   ---   FILE: {fname}")
				
				#if NEW or CHANGED, put it in verDir
				if (not os.path.exists(oldPath)) or (not filecmp.cmp(oldPath, newPath)):
					verPath = os.path.join(verDir, relpath, fname)
					fuckinMakeTheDirectoryOkay(verPath)
					shutil.move(newPath, verPath)
					if os.path.exists(oldPath):
						print(f"   ----   CHANGED! USING {verPath} AND {oldPath}")
						shutil.copy2(oldPath, newPath)
					else:
						print(f"   ----   NEW! USING {verPath}")
	
	#Any files in old but removed in new? Too bad. That literally won't work here.

##----

if len(sys.argv) <= 1:
	ver = input('game ver (e.g. 1.1)? ')
else:
	ver = sys.argv[1]
	
if len(sys.argv) <= 2:
	new = input('new ModFolder? ')
else:
	new = sys.argv[2]
if not os.path.isdir(new):
	sys.exit(f"{new} is not a directory?")
	
if len(sys.argv) <= 3:
	old = input('Old ModFolder? ')
else:
	old = sys.argv[3]
if not os.path.isdir(old):
	sys.exit(f"{old} is not a directory?")

doSquash(ver, new, old)