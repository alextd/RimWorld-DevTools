# RimWorld mod multiversioning support.
# Separate the PATCH process from your BUILD process.
# Build your 1.x mod as if it only supported 1.x
# Keep an old 1.0 (and 1.0/1.1) mod release as a base.
# Then use this tool to make the release version for 1.0 + 1.x
#
# The basic target structure is for all 1.0 files to go in the root Mod/
# Any new or changed content ends up in Mod/1.x
# Preserving any Mod/1.1 folders already existing
# LoadFolders.xml should specify 1.2 -> 1.1 -> / so new files in 1.1 are included in 1.2
#  *Note: Assemblies is handled by blindly copying into 1.0/1.x folders, since 1.x removed Harmony.dll 
#	 *Note: This also doesn't support removing files
#
#  python squashRelease.py Version ModNew ModOld
#  (python3 of course)
#
# This tool squashes a 1.1-only NewMod folder and a 1.0 OldMod folder to make a dual-version NewMod folder.
# NewMod is renamed " - Patching" and OldMod is copied into its place
# Unchanged files are kept in NewMod/ (and possibly intermediary NewMod/1.1, etc.)
# Changed files are detected and go in NewMod/1.x/
# Then New files are detected and put in NewMod/1.x/
# The resulting NewMod folder should have a suitable release for 1.1/1.0 with no duplicate copies.
#
# The entire About/ + LoadFolders.xml is simply taken from 1.x
# (Though PublishedFileId.txt is recovered first)
# Note: The About.xml is not edited, so it should just lie and include all latest versions 1.x, 1.1, 1.0 etc.
#  even though it only does 1.x originally
#
## --------------
#
#  HOW TO:
# Step 1: Keep a static, unchanging copy of the 1.0 release in ModOld
# Step 2: Build 1.1 version in ModNew ready for release, with no 1.0 support
# Step 3: Squash them together - now the ModNew folder supports 1.1 and 1.0
# ...
# Step 4: Keep that 1.1/1.0 release, and squash 1.x onto it too.
#
# Future 1.x mod updates should be done with a fresh 1.x build, squashed onto the original base folder
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
	if not os.path.exists(new):
		print(f"--  !Nope! new dir does not exist.")
		return
	
	#Let's not squash twice. It needs clean and rebuild
	dirPatch = os.path.join(new, ver)
	if os.path.exists(dirPatch):
		print(f"--  !Nope! Already Squashed it.")
		return
	
	if not os.path.exists(old):
		print(f"--  !Nope! Old dir does not exist.")
		return
		
	#Move build folder to temp folder, copy in old to replace it
	dirBuild = new+" - Patching"
	if os.path.exists(dirBuild):
		print(f"--  !Nope! Clean up your past Patch attempt!.")
		return
	os.rename(new, dirBuild)
	dirMerge = shutil.copytree(old, new)
	#dirMerge = base + 1.1, etc; now squashing dirBuild into dirPatch to make it merged up to 1.x
	os.mkdir(dirPatch)
	
	print(f"  --  New changes going into {dirPatch}")
	
	#Copy in the About folder / LoadFolders - full replacement (plus PublishedFileId.txt)
	aboutMerge = os.path.join(dirMerge, "About")
	aboutBuild = os.path.join(dirBuild, "About")
	os.rename(os.path.join(aboutMerge, "PublishedFileId.txt"), os.path.join(aboutBuild, "PublishedFileId.txt"))
	shutil.rmtree(aboutMerge)
	os.rename(aboutBuild, aboutMerge)
	os.replace(os.path.join(dirBuild, "LoadFolders.xml"), os.path.join(dirMerge, "LoadFolders.xml"))
	
	#Copy Assemblies to 1.x folder.
	# Since Harmony was in 1.0 but no longer in 1.x, is it a **removed** file which this script doesn't handle.
	# So handle it here by forcing Assemblies to each version folder. They'll change anyway, right?
	# (Assuming the old ver has done this already too if it includes 1.1)
	newAss = os.path.join(dirBuild, "Assemblies")
	if os.path.exists(newAss):
		os.rename(newAss, os.path.join(dirPatch, "Assemblies"))
		
	#Now look in the merged folder, for any changed files in 1.x.
	#Check only the latest version for change to include
	#Remove files from dirBuild as they are 
	
	#Dictionary of files : latest patch
	modFiles = {}
			
	#Construct dictionary! Find all files in old mod.
	for dname, dirs, files in os.walk(dirMerge):
		#Special cases.
		#About is just overwritten, not put in version folders
		#Assemblies handled above manually via full copy.
		#1.x patch folders are handled in their own loop.
		if "About" in dname or "Assemblies" in dname:
			continue
			
		print(f" - {dname}")
			
		#Find the relative path inside the mod folder
		relpath = str(PurePath(dname).relative_to(dirMerge))
		
		version = 1
		if relpath.startswith("1."):
			version = float(relpath[0:3])
			relpath = relpath[4:]
		
		for file in files:
			if file == "LoadFolders.xml":
				continue
				
			resolvedFile = os.path.join(relpath, file)
			print(f"   ---   FILE: {resolvedFile} ({version})")
			if not resolvedFile in modFiles or modFiles[resolvedFile] <= version:
				modFiles[resolvedFile] = version
			
	#find changed files in 1.x
	for file in modFiles:
		latestVer = modFiles[file]
	
		
		newPath = os.path.join(dirBuild, file)
		print(f" - CHECKING: {file} ({latestVer})")
		if not os.path.exists(newPath):
			continue
		
		if latestVer == 1:
			oldPath = os.path.join(dirMerge, file)
		else:
			oldPath = os.path.join(dirMerge, str(latestVer), file)
		
		if filecmp.cmp(oldPath, newPath):
			#Remove from dirBuild just so it's not confused as a new file later
			os.remove(newPath)
			print(f"   ----   SAME! USING {oldPath}")
		else:
			#CHANGED, put it in dirPatch
			verPath = os.path.join(dirPatch, file)
			fuckinMakeTheDirectoryOkay(verPath)
			shutil.move(newPath, verPath)
			print(f"   ----   CHANGED! USING {verPath} AND {oldPath}")
	
	#find new files in 1.x. Just put em in ! easy.
	
	for dname, dirs, files in os.walk(dirBuild):
	
		#Find the relative path inside the mod folder
		relpath = str(PurePath(dname).relative_to(dirBuild))
		for file in files:
			filePath = os.path.join(dname, file)
			verPath = os.path.join(dirPatch, relpath, file)
			fuckinMakeTheDirectoryOkay(verPath)
			os.rename(filePath, verPath)
			print(f"   ----   NEW! USING {verPath}")

	shutil.rmtree(dirBuild)
	#done!
	
	
	#TODO: Any files in old but removed in new?... Let's hope not

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