# Sets up a RimWorld C# project to be translatable
#python translateRimworldMod.py ModFolder
#
# Reads C# Source files for Strings
# Creates XML for translation
# Inserts Translation calls back into Source
# (do keep backups, this will re-write all your files)
#
# Can call again and it will insert new lines into XML and find untranslated strings in source
#
#It shows a line, a string to translate, and prompts for translation xml tag name
#	- It defaults a suggested xml tag
# - Set the prompt to blank to pass and do nothing (if you have typewrite installed)
# - It searches Core translation xmls and uses that if it exists
# - It does NOT suggest a default if there's a core translation that's lowercased
# - Repeated strings use same xml tag and are not prompted for again
# - Set to 'n' to add to a global no-translate list (in "noTranslate.txt")
#
#You can make a "translateTag.txt" file with your name to tag all translatestrings as "tag.string"
#
#Certain lines are skipped, like HarmonyPatch() and Log.Message, see def process
#

try:
	import pyautogui
except:
	print("No typewrite!")
	pass
import os
import sys
import re 
import shutil
import glob
from xml.sax.saxutils import escape

xmlBegin = """<?xml version="1.0" encoding="utf-8" ?>
<LanguageData>
	
"""
xmlEnd = """	
</LanguageData>"""

tag = ""
if os.path.exists ("translateTag.txt"):
	with open("translateTag.txt") as file:
		tag = file.read() + "."
		print(f"Tag is {tag}")
	
	
#Find already-used strings from Core English translations
#Don't Make XML entries, but do .Translate them.
coreTr = {} # e.g. coreTr["A phrase to transate"] = "APhraseToTranslate" (and then print .Translate() after)
coreTrRE = re.compile("<([^/!][^>]*)>([^<]*)</")
for dname, dirs, files in os.walk("Core/Languages/English/Keyed"):
	for fname in files:
		with open(os.path.join(dname, fname), 'r') as f:
			for line in f.readlines():
				match = re.search(coreTrRE, line)
				if match is not None:
					#Add this Core string
					if match.group(2) in coreTr:
						if len(coreTr[match.group(2)]) <= len(match.group(1)):
							#Use previous match, shorter.
							continue
							
					coreTr[match.group(2)] = match.group(1)

#TODO: also walk "Mod/Langauges"?
					

def fuckinMakeTheDirectoryOkay(outfilename):
	try:
		os.makedirs(os.path.dirname(outfilename))
	except:
		pass

		
matchUntaggedXMLRE = re.compile(r"(?:  |	)<(?!{0})(.*)>(.*)</.*>".format(tag))
noTrF = open("noTranslate.txt", "a+")
noTrF.seek(0, os.SEEK_SET)
content = noTrF.read()
noTrStrings = content.splitlines()
noTrF.seek(0,os.SEEK_END)
def doKeyed(dir):
	if not os.path.isdir(dir):
		print("'{dir}' is not a directory")
		sys.exit(0)
		
	outfilename = os.path.join(dir, "Languages\English\Keyed\AutoEnglish.xml");
	print(f"   ---   Writing to {outfilename}")
	fuckinMakeTheDirectoryOkay(outfilename)
	
	existsXml = os.path.isfile(outfilename)
	if existsXml:
		if tag != "":
			with open(outfilename, "r+") as original:
				lines = original.readlines()
				original.seek(0)
				for line in lines:
					line = re.sub(matchUntaggedXMLRE, r"	<{0}\1>\2</{0}\1>".format(tag), line)
					original.write(line)
		outfile = open(outfilename, "r+")
		outfile.seek(0, os.SEEK_END)
		outfile.seek(outfile.tell() - len(xmlEnd) - 1, os.SEEK_SET)#2 is from end enum
	else:
		outfile = open(outfilename, "w")
		outfile.write(xmlBegin)
		
	for dname, dirs, files in os.walk(dir):
		for fname in files:
			if fname.split(os.extsep)[-1] != "cs":
				continue
			print(f"   ---   FILE: {fname}")
			fpath = os.path.join(dname, fname)
			with open(fpath, 'r+') as f:
				old = f.readlines()
				f.seek(0)
				for line in old:
					line = process(line, outfile)
					f.write(line)
				f.truncate()
	
	outfile.write(xmlEnd)


matchString = r'(.*?)(?:\$)?"(?!.Translate)([^"]*)"(?!.Translate)(.*)'
matchQuoteRE = re.compile(matchString)

matchFmtRE = re.compile("{([^}]*)}")
class NextFmt:  # On Py2, use class Replacer(object): to explicitly use new style classes
	def __init__(self):
		self.i = 0
	def __call__(self, matchobj):
		result = "{%d}" % self.i
		self.i += 1
		return result
		
xmlTagBadRE = re.compile("[^a-zA-Z0-9-_.]")
def makeXmlTag (str): 
	stripped = [re.subn(xmlTagBadRE, "", word) for word in str.split(" ")]
	return "".join([word.capitalize() for (word, _) in stripped])
	
	
stringCodes = {}
def process(line, outfile):
	if "Harmony" in line: return line
	if "Log." in line: return line
	if "AccessTools." in line: return line
	if "System.Diagnostics." in line: return line
	if "DebugLog" in line: return line
	if "Scribe" in line: return line
	if "[assembly" in line: return line
	if "ContentFinder" in line: return line
	if "Resources" in line: return line
	if "typeof" in line: return line
	if line.strip().startswith("//"): return line
	if line.strip().startswith("/*"): return line
	
	matchRE = matchQuoteRE
	match = re.search(matchRE, line)
	while match is not None:
		thisTag = tag
		ostr = match.group(2)
		if ostr == "": break
		
		str = ostr
		
		#find {value} formats
		formatVars = re.findall(matchFmtRE, str)
		if len(formatVars) > 0:
			(str, _) = re.subn(matchFmtRE, NextFmt(), str)
		
		#Find translateStr to insert
		translateStr = None
		if ostr in noTrStrings:
			translateStr="" #Act as if input skipped
		elif str in stringCodes:
			#Already made it 
			print (f"  --  Using previous tag for {str}")
			translateStr = stringCodes[str]
		elif str in coreTr:
			print ("")
			print (line.strip())
			try:
				pyautogui.typewrite("y")
			except:
				pass
			if input(f'Use Core <{coreTr[str]}> for "{str}"? (y)\n:') == "y":			
				thisTag = ""
				translateStr = coreTr[str]
		
		#Ask user for translateStr
		newStr = False
		if translateStr is None:
			newStr = True
			#Ask for input, what goes in <TrTag>
			print ("")
			print (line.strip())
			print ("")
			
			#insert suggestion
			if str.lower() in coreTr or str.lower().capitalize() in coreTr:
				print("NOTE: (lower-case version is in Core)");
			else:
				try:
					pyautogui.typewrite(makeXmlTag(str))
				except:
					pass
			translateStr = input('"' + str + '"\n:')
		
		#Insert translateStr into the line
		if len(translateStr) == 0 or translateStr == "n":
			#No translation
			if translateStr == "n":
				#Never translate, write to file
				noTrF.write(ostr + "\n")
				noTrStrings.append(ostr)
				
			#But there might be more on the same line, so:
			#directly add the untranslated string to the RE to match the next quote instead
			matchRE = re.compile("("+re.escape(match.group(1) + '"' + ostr + '"') + matchString[1:])
			match = re.search(matchRE, line)
			continue
		
		if newStr:
			#Apply translation, write to xml
			stringCodes[str] = translateStr
			print ("	<{2}{0}>{1}</{2}{0}>".format(translateStr, escape(str), thisTag), file=outfile)
				
		#replace line in code with "...".Translate()
		line = re.sub(matchRE, r'\1"{1}{0}".Translate({2})\3'.format(translateStr, thisTag, ", ".join(formatVars)), line)
		match = re.search(matchRE, line)
	return line
	
if len(sys.argv) == 1:
	dir = input('mod dir?')
else:
	dir = sys.argv[1]

doKeyed(dir)