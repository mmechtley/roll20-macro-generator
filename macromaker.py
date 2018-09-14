import sys
import datetime
import string
import os

# Listen, this aint pretty, but for now it works.
# This is real code. It might not be ideal, but this is what peak performance looks like.
# Maybe moderate performance.
# Improve it if you want it's all open source for you to do whatever with.

def hasNumbers(str):
	return any(char.isdigit() for char in str)

def isNumber(word):
	test = word.replace("+", "").replace("-", "").replace("d", "")
	return all(char.isdigit() for char in test)

def getNumber(data):
	for word in data:
		if (isNumber(word)):
			return ensurePlus(word)
	return ""

def getWord(data, ignore = "", ignore2 = ""):
	for word in data:
		if (word != ignore and word != ignore2):
			if (isNumber(word)):
				continue
			else:
				return word
	return ""

def parseDamageType(data):
	if ("/" in data):
		return data.upper()
	else:
		return data.capitalize()

def ensurePlus(data):
	if ("d" in data):
		return data
	if ("-" in data):
		return data
	if ("+" not in data):
		return "+" + data
	return data

def increaseDie(data, amount = 1):
	if ("d" not in data):
		num = int(data)
		num *= amount
		return num

	split = data.split("d")
	numDice = int(split[0])
	numDice *= amount
	return "%sd%s" % (numDice, split[1])

def generatePrompt(data):
	if (configPrompts):
		return data
	return "0"

def wrapDice(data):
	if ("d" in data):
		if (isNumber(data)):
			return "[[%s]]" % (data)
	return data

if (len(sys.argv) > 1):
	infiles = [str(sys.argv[1])]
else:
	indir = os.path.dirname(os.path.realpath(__file__))
	infiles = os.listdir(indir)

keywordsDamage = ["p", "s", "p/s", "b", "bludgeoning", "piercing", "slashing", "acid", "cold", "electricity", "elec", "fire", "sonic", "force", "precision", "negative", "positive", "pos", "neg", "mental", "chaotic", "evil", "good", "lawful", "heal", "healing"]
keywordsAttack = ["melee", "ranged"]
keywordsHealing = ["pos", "positive", "healing", "heal"]

saveTypes = ["fort", "ref", "will"]
abilityTypes = ["str", "dex", "con", "int", "wis", "cha"]


for infile in infiles:
	if ("-macros" in infile):
		continue
	if (not infile.endswith(".txt")):
		continue
	with open(infile, 'r') as file:
		configPrompts = True

		contents = file.read()
		firstMacro = contents.find('>')
		conents = contents[firstMacro:]

		data = conents.split("\n>")
		macro = "# Generating macros from %s %s\n\n" % (file.name, datetime.datetime.now())

		for d in data:
			lines = d.strip(">").split("\n")
			
			damage = ""
			footer = ""
			skills = ""
			comment = ""
			canCrit = False
			isSkill = False
			isInit = False
			isAbility = False
			isSave = False
			isDamage = True
			deadly = ""
			hasTitle = False
			damageLabel = "damage"
			blanks = ""
			bullets = "&bull;"

			for line in lines:
				if (line == ""):
					continue

				if (line[0] == "#"):
					continue

				linedata = line.split("#")[0].strip();

				if (linedata.startswith("config:")):
					commandline = linedata.split(":")[1]
					commandsplit = commandline.split("=")
					command = commandsplit[0].strip()
					setting = commandsplit[1].strip()
					if (command == "prompts"):
						if (setting == "off"):
							configPrompts = False
					continue

				if (not hasTitle):
					title = linedata.upper()
					macro += "# %s\n&{template:default} {{name=&#9658; **%s**}} " % (linedata.upper(), string.capwords(linedata))

					if (title == "SKILLS"):
						skills = "?{Skill"

					if (title == "ABILITY"):
						skills = "?{Ability"

					if (title == "SAVES"):
						skills = "?{Save"

					hasTitle = True
					continue

				if (".jpg" in linedata or ".png" in linedata or ".gif" in linedata):
					macro += "{{%s=[x](%s)}}" % (blanks, linedata)
					blanks += "&#8203;"
					continue;

				if (linedata.startswith("*")):
					footer += "{{%s=*%s*}} " % (bullets, linedata.strip("*").strip())
					bullets += "&#8203;"
					continue

				if (":" in linedata):
					split = linedata.split(":")
					words = split[1].split(" ")
					rightside = ""
					for word in words:
						rightside += parseDamageType(wrapDice(word)) + " "

					footer += "{{%s=%s}}" % (string.capwords(split[0].strip()), rightside.strip())
					continue

				words = linedata.strip().split(" ")

				intersect = set(keywordsAttack).intersection(set(words))
				if (len(intersect) > 0):
					attackType = intersect.pop()
					canCrit = True

					mapenalty = "?{MAP|0|-5|-10}[MAP]"
					if ("agile" in words):
						mapenalty = "?{MAP|0|-4|-8}[MAP]"

					info = ""
					if ("touch" in words):
						info += "Touch "

					hitBonus = getNumber(words)

					macro += "{{%s=[[d20%s[Hit]+%s+%s]] %s}} " % (attackType, hitBonus, mapenalty, generatePrompt("?{Hit Bonus|0}[Bonus]"), info.strip())

				if ("range" in words):
					macro += "{{range=%s}} " % (string.capwords(line.split(" ", 1)[1]))

				if ("sneak" in words):
					footer += "{{Sneak Attack=[[%s]]}} " % (getNumber(words))

				if ("extra" in words):
					footer += "{{Extra Damage=[[%s]] %s}} " % (getNumber(words), getWord(words, "extra"))

				if ("save" in words):
					footer += "{{Save=%s %s}} " % (getWord(words, "save").capitalize(), getNumber(words).strip("+"))

				if ("deadly" in words):
					deadly += " [[%s]] Deadly" % (getNumber(words))

				# Okay I got really lazy for the heightening parts sorry

				if ("heighten+1" in words):
					times = 1

					macroLabel = "Heighten"
					if ("persist" in words):
						macroLabel = "Hgt Persist"

					heighten = getNumber(words)
					heightenMacro = "?{%s|0," % (macroLabel)
					for x in range(1, 11, 1):
						number = increaseDie(heighten, times)
						secondNumber = number;
						if ("persist" in words):
							secondNumber = "**%s**" % (number)

						heightenMacro += "|%s (+%s),%s" % (x, number, secondNumber)
						times += 1

					if ("persist" in words):
						footer += "{{Heightened&#8203;=+%s} %s}}" % (heightenMacro, getWord(words, "heighten+1", "persist").capitalize())
					else:
						footer += "{{Heightened=[[%s}]] %s}}" % (heightenMacro, getWord(words, "heighten+1").capitalize())
				elif ("heighten+2" in words): # Oh man this is so bad haha
					times = 1

					macroLabel = "Heighten"
					if ("persist" in words):
						macroLabel = "Hgt Persist"

					heighten = getNumber(words)
					heightenMacro = "?{%s|0," % (macroLabel)
					for x in range(2, 11, 2):
						number = increaseDie(heighten, times)
						secondNumber = number;
						if ("persist" in words):
							secondNumber = "**%s**" % (number)

						heightenMacro += "|%s (+%s),%s" % (x, number, secondNumber)
						times += 1

					if ("persist" in words):
						footer += "{{Heightened&#8203;=+%s} %s}}" % (heightenMacro, getWord(words, "heighten+2", "persist").capitalize())
					else:
						footer += "{{Heightened=[[%s}]] %s}}" % (heightenMacro, getWord(words, "heighten+2").capitalize())
				elif ("persist" in words): # Sorry
					footer += "{{Persist=**%s** %s}} " % (getNumber(words), parseDamageType(getWord(words, "persist")))
				else: # But it works!
					intersect = set(keywordsDamage).intersection(set(words))

					if (len(intersect) > 0):
						damageType = parseDamageType(intersect.pop())
						damagePrompt = generatePrompt("?{%s Bonus|0}" % (damageType))
						damage += "[[%s+%s]] %s " % (getNumber(words), damagePrompt, damageType)
						if (damageType.lower() in keywordsHealing):
							damageLabel = "Healing"
							canCrit = False


				if (title == "SKILLS"):
					isSkill = True
					isDamage = False

					skills += "|%s (%s),%s" % (string.capwords(getWord(words)), getNumber(words), getNumber(words))

				if (title == "ABILITY"):
					isAbility = True
					isDamage = False

					if (len(words) == 6):
						scores = words.copy()
						parseIndex = 0;

						for score in scores:
							skills += "|%s (%s),%s" % (abilityTypes[parseIndex].capitalize(), ensurePlus(score), ensurePlus(score))
							parseIndex += 1
						continue

					label = string.capwords(getWord(words))
					if (label == ""):
						label = abilityTypes[parseIndex].capitalize()

					skills += "|%s (%s),%s" % (label, getNumber(words), getNumber(words))
					
				if (title == "SAVES"):
					isSave = True
					isDamage = False

					if (len(words) == 3):
						scores = words.copy()
						parseIndex = 0;

						for score in scores:
							skills += "|%s (%s),%s" % (saveTypes[parseIndex].capitalize(), ensurePlus(score), ensurePlus(score))
							parseIndex += 1
						continue

					label = string.capwords(getWord(words))
					if (label == ""):
						label = saveTypes[parseIndex].capitalize()

					skills += "|%s (%s),%s" % (label, getNumber(words), getNumber(words))

			if (isDamage):
				if (damage.strip() != ""):
					macro += "{{%s=%s}} " % (damageLabel, damage.strip())

			if (canCrit):
				if (damage.strip() != ""):
					macro += "{{critical=%s%s}} " % (damage.strip(), deadly)
			
			if (isSkill):
				macro += "{{Check=[[d20+%s}+%s]]}} " % (skills, generatePrompt("?{Skill Bonus|0}"))

			if (isAbility):
				macro += "{{Ability Check=[[d20+%s}+%s]]}} " % (skills, generatePrompt("?{Ability Bonus|0}"))

			if (isSave):
				macro += "{{Save=[[d20+%s}+%s]]}} " % (skills, generatePrompt("?{Save Bonus|0}"))



			macro += footer.strip()
			macro = macro.strip() + "\n\n"

			# Repeat Skills to generate Initiative macro
			if (isSkill):
				macro += "# INITATIVE\n&{template:default} {{name=Initiative}} "
				macro += "{{Initative=[[d20+%s}+%s &{tracker}]]}}\n\n" % (skills, generatePrompt("?{Skill Bonus|0}"))

		outfile = open("_%s-macros.txt" % (infile.split(".")[0]), "w")
		outfile.write(macro.strip())
		outfile.close()