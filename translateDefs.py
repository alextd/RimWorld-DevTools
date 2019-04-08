#Generate sample XML translations for RimWorld defs
#python translateDefs.py ModFolder
#
# Reads Def Xmls for reportString, label, and others
# Creates sample XML files for translation in Languages/Sample/DefInjected/*Def/
# (I don't who/what/how translators use but basically: copy /Sample to /Spanish and edit)
#	Replaces those files with each run
#
# TODO:
# Handle tags in lists

import os
import sys
import re 
import shutil

xmlBegin = """<?xml version="1.0" encoding="utf-8" ?>
<LanguageData>
	
"""
xmlEnd = """	
</LanguageData>"""

def fuckinMakeTheDirectoryOkay(outfilename):
	try:
		os.makedirs(os.path.dirname(outfilename))
	except:
		pass

endDefTagRE = re.compile(r"</[^<>]*Def>")	
defTagRE = re.compile(r"<([^/<>]*Def)[^>]*>")
defNameRE = re.compile(r"<defName>([^<>]*)</defName>")
xmlTagSTR = r"<{0}>([^<>]*)</{0}>"

translateTags = ["reportString", "label", "description",
	"recoveryMessage", "beginLetter", "baseInspectLine"]

def doDefInjected(dir):
	if not os.path.isdir(dir):
		print (f"'{dir}' is not a directory")
		sys.exit(0)
		
	defsDir = os.path.join(dir, "Defs");
	defs = {}	
	for dname, dirs, files in os.walk(defsDir):
		for fname in files:
			if fname.split(os.extsep)[-1] != "xml":
				continue
			print	(f"   ---   FILE: {fname}")
			fpath = os.path.join(dname, fname)
			with open(fpath, 'r+') as f:
				curDef = ""
				curDefName = ""
				for line in f:
						
					match = re.search(defTagRE, line)
					if match is not None:
						curDef = match.group(1)
						print	(f"   ---   DEF: {curDef}")
						if curDef not in defs:
							defs[curDef] = []
						continue
						
					match = re.search(defNameRE, line)
					if match is not None:
						if curDef is not "":
							curDefName = match.group(1)
							print	(f"   ---   NAME: {curDefName}")
						continue
						
					for tag in translateTags:
						match = re.search(xmlTagSTR.format(tag), line)
						if match is not None:
							print	(f"   ---   XML: {tag}")
							if curDefName is not "":
								defs[curDef].append((curDefName, tag, match.group(1)))
						continue
						
					match = re.search(endDefTagRE, line)
					if match is not None:
						curDef = ""
						continue
					
						
	defInjectedDir = os.path.join(dir, "Languages\Sample\DefInjected")	
	for defTag, list in defs.items():
		if len(list) == 0:
			continue
			
		defTagDir = os.path.join(defInjectedDir, defTag)
		defTagXml = os.path.join(defTagDir, "Sample"+defTag+"Injected.xml")
		
		fuckinMakeTheDirectoryOkay(defTagXml)
		print (f"   ---   Writing Sample to {defTagXml}")
		with open(defTagXml, "w") as deftagfile:
			deftagfile.write(xmlBegin)
			for defName, tag, value in list:
				deftagfile.write("	<{0}.{1}>{2}</{0}.{1}>\n" .format (defName, tag, value))
			deftagfile.write(xmlEnd)
		
if len(sys.argv) == 1:
	print ("need dir as argv")
	sys.exit(0)

doDefInjected(sys.argv[1])