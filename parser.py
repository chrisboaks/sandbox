# These functions will allow you to
#   - Read in Prison Architect save files
#   - Modify the read content
#   - Save content back into Prison Architect save file formats


import re
from collections import OrderedDict
# from pprint import PrettyPrinter


TOKEN_BEGIN = 1
TOKEN_END = 2
TOKEN_CONTENT = 3

CATEGORY_PROTECTED = "Protected"
CATEGORY_MINSEC = "MinSec"
CATEGORY_MEDSEC = "Normal"
CATEGORY_MAXSEC = "MaxSec"
CATEGORY_SUPERMAX = "SuperMax"
PRISONER_CATEGORIES = (CATEGORY_PROTECTED, CATEGORY_MINSEC, CATEGORY_MEDSEC, CATEGORY_MAXSEC, CATEGORY_SUPERMAX)

RELEASED = "Released"

DANGEROUS_REPUTATIONS = set(("Volatile", "Instigator", "CopKiller", "Deadly"))
DANGEROUS_MISCONDUCTS = set(("InjuredPrisoner", "InjuredStaff", "Murder", "Destruction"))


def parse_tokens(tokens):
    content = OrderedDict()
    index = 0
    if type(tokens) is list:
        tokens = enumerate(tokens)
    for index, token in tokens:
        if token[0] == TOKEN_END:
            break
        elif token[0] == TOKEN_BEGIN:
            secondIndex, secondToken = next(tokens)
            if secondToken[0] != TOKEN_CONTENT:
                raise Exception("Expected a CONTENT token after a BEGIN token")
            parsed_tokens, sub_contentLength = parse_tokens(tokens)
            content.setdefault(secondToken[1].strip('"'), [])
            content[secondToken[1].strip('"')].append(parsed_tokens)
        else:
            secondIndex, secondToken = next(tokens)
            content.setdefault(token[1].strip('"'), [])
            content[token[1].strip('"')].append(secondToken[1])
    return content, index


def escaped(name):
    return ('"%s"' % name) if " " in name else name


def generate_prison_format(parsed_prison, indent=0):
    content = []
    for name, values in parsed_prison.iteritems():
        for value in values:
            if type(value) is OrderedDict:
                sub_content = generate_prison_format(value, indent + 1)
                if len(sub_content) >= 2:
                    content.append("BEGIN %s" % escaped(name))
                    for subEntry in sub_content:
                        content.append("".join(("   ", subEntry)))
                    content.append("END")
                else:
                    content.append("BEGIN %s END" % " ".join([escaped(name)] + sub_content))
            else:
                content.append(" ".join((escaped(name), str(value))))
    return content


def security_hearings(parsed_prison):
    for id, entry in parsed_prison["Objects"][0].iteritems():
        if type(entry[0]) == OrderedDict and entry[0].get("Type", None) == ["Prisoner"]:
            prisoner_grade = grade_prisoner(parsed_prison, id, entry)
            if prisoner_grade == RELEASED:
                print "EARLY PAROLE FOR", id
                entry[0]["Bio"][0]["Sentence"][0] = float(entry[0]["Bio"][0]["Served"][0])
            elif prisoner_grade is not None:
                if entry[0]["Category"][0] != prisoner_grade:
                    print "CHANGING", id, "FROM", entry[0]["Category"][0], "TO", prisoner_grade
                entry[0]["Category"][0] = prisoner_grade


def grade_prisoner(parsed_prison, id, entry):

    # Don't grade unrevealed prisoners
    reputation_revealed = entry[0]["Bio"][0].get("ReputationRevealed", False)
    if not reputation_revealed:
        return

    # Collect relevant prisoner information
    days_in_prison = float(entry[0]["Experience"][0]["Experience"][0]["TotalTime"][0].rstrip(".")) / 1440
    sentence = float(entry[0]["Bio"][0].get("Sentence", [100])[0])
    served = float(entry[0]["Bio"][0].get("Served", [0])[0])
    # parole = float(entry[0]["Bio"][0]["NextParole"][0])
    reputations = set(entry[0]["Bio"][0].get("Reputation", []))
    high_reputations = set(entry[0]["Bio"][0].get("ReputationHigh", []))
    programs_passed = sum(int(program[0].get("Passed", [0])[0]) for program in entry[0]["Experience"][0]["Results"][0].values())
    dangerous = reputations & DANGEROUS_REPUTATIONS or high_reputations & DANGEROUS_REPUTATIONS
    try:
        misconducts = len([
            True
            for misconduct in parsed_prison["Misconduct"][0]["MisconductReports"][0][id][0]["MisconductEntries"][0].values()
            if type(misconduct[0]) is OrderedDict and misconduct[0]["Convicted"][0] == "true"
        ])
    except KeyError:
        misconducts = 0
    try:
        violent_behavior = len([
            True
            for misconduct in parsed_prison["Misconduct"][0]["MisconductReports"][0][id][0]["MisconductEntries"][0].values()
            if type(misconduct[0]) is OrderedDict and misconduct[0]["Type"][0] in DANGEROUS_MISCONDUCTS
        ])
    except KeyError:
        violent_behavior = 0

    # Grading a prisoner costs $100
    parsed_prison["Finance"][0]["Balance"][0] = "%g" % (float(parsed_prison["Finance"][0]["Balance"][0]) - 100)

    # Consider early release for well-behaved prisoners
    # if not dangerous and not violent_behavior and served + programs_passed > parole + misconducts and programs_passed - misconducts > 2:
    if not dangerous and not violent_behavior and served + programs_passed > misconducts and programs_passed - misconducts > 2:
        parsed_prison["Finance"][0]["Balance"][0] = "%g" % (float(parsed_prison["Finance"][0]["Balance"][0]) + 1000)
        return RELEASED

    # Don't recategorize Protected prisoners
    category = entry[0]["Category"][0]
    if category == CATEGORY_PROTECTED:
        return

    # Violent or dangerous MinSec prisoners will get boosted up to MedSec
    if category == CATEGORY_MINSEC:
        return CATEGORY_MEDSEC if violent_behavior or dangerous else CATEGORY_MINSEC

    # Legendary prisoners have two options: MaxSec or SuperMax
    if "Legendary" in high_reputations:
        if violent_behavior or dangerous:
            return CATEGORY_SUPERMAX
        else:
            return CATEGORY_MAXSEC if days_in_prison > 8 else category

    # All others have two options: MedSec or MaxSec
    else:
        if violent_behavior or dangerous:
            return CATEGORY_MAXSEC
        else:
            return CATEGORY_MEDSEC if days_in_prison > 4 else category


inFile = r"orig.prison"
outFile = r"parsed.prison"
with open(inFile, "r") as oldPrisonFile, open(outFile, "w") as newPrisonFile:
    scanner = re.Scanner([
        (r"\s+", None),
        (r"BEGIN", lambda scanner, token:(TOKEN_BEGIN, token)),
        (r"END", lambda scanner, token:(TOKEN_END, token)),
        (r'".*"', lambda scanner, token:(TOKEN_CONTENT, token)),
        (r"[^\s]*", lambda scanner, token:(TOKEN_CONTENT, token)),
    ])

    tokens, remainder = scanner.scan(oldPrisonFile.read())
    parsed_prison = parse_tokens(tokens)[0]

    security_hearings(parsed_prison)
    newPrisonFile.write("\n".join(generate_prison_format(parsed_prison)))
