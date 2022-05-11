#dependencies: pip install python-dotenv gql requests requests_toolbelt pydantic beautifulsoup4
from dotenv import dotenv_values
from bs4 import BeautifulSoup
import re
import csv
import os
import requests
import json

    
env_config = dotenv_values("sample.env")

def get_techniques_from_csv(csv_path):
    technqs = set()
    with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not "TA" in row[0]:
                technqs.add(row[0])
    return technqs

def technique_to_mitre_path(technique_set):
    new_technique_set = set()
    for technique in technique_set:
        if "." in technique:
            new_tech = technique.replace(".","/")
            new_technique_set.add(new_tech)
        else :
            new_technique_set.add(technique)
    return new_technique_set
    
def get_apt_name(csv_path):
    filename = os.path.basename(csv_path)
    apt_name = os.path.splitext(filename)[0]
    return apt_name
    
def get_test_case_tuples(url_ready_tech_set):
    # Tuple needs to have name ("APT Name - Technique Name"), tactic/phase name, technique number
    tuple_list = []
    mitre_technique_url ="https://attack.mitre.org/techniques/"
    for tech in url_ready_tech_set:
        url = mitre_technique_url + tech + "/"
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        tactic = soup.find("span", attrs={"class": "h5 card-title"}, string=re.compile("(Tactic)s*(:)")).find_next_sibling("a").get_text()
        tactic = tactic.lower().replace(" ", "-")
        dot_tech = tech.replace("/", ".")
        tac_tech_tuple = (dot_tech, tactic)
        tuple_list.append(tac_tech_tuple)
    return tuple_list

def get_techniques_json(testcase_tuples) :
    techniques = []
    for tech_tuple in testcase_tuples:
        tech_json = {
            "techniqueID": tech_tuple[0],
            "tactic": tech_tuple[1],
            "score": 1,
            "color": "",
            "comment": "",
            "enabled": True,
            "metadata": [],
            "links": [],
            "showSubtechniques": False
        }
        techniques.append(tech_json)
    #technique_json = (json.dumps(techniques))
    return techniques
    
def write_json_to_file(technique_json_final):
    filename = get_apt_name(csv_path=env_config.get("CSV_PATH")) + ".json"
    with open(filename, 'w') as f:
        f.write(technique_json_final)
    print("Json data written to file %s " % (filename))

target_db = env_config.get("TARGET_DB")

techniques = get_techniques_from_csv(csv_path=env_config.get("CSV_PATH"))

url_ready_techniques = technique_to_mitre_path(techniques)

apt_name = get_apt_name(csv_path=env_config.get("CSV_PATH"))

testcase_tuples = get_test_case_tuples(url_ready_techniques)

techniques_json = get_techniques_json(testcase_tuples)

export_json = {
	"name": apt_name,
	"versions": {
		"attack": "11",
		"navigator": "4.6.1",
		"layer": "4.3"
	},
	"domain": "enterprise-attack",
	"description": "",
	"filters": {
		"platforms": [
			"Linux",
			"macOS",
			"Windows",
			"PRE",
			"Containers",
			"Network",
			"Office 365",
			"SaaS",
			"Google Workspace",
			"IaaS",
			"Azure AD"
		]
	},
	"sorting": 0,
	"layout": {
		"layout": "side",
		"aggregateFunction": "average",
		"showID": False,
		"showName": True,
		"showAggregateScores": False,
		"countUnscored": False
	},
	"hideDisabled": False,
	"techniques": 
		techniques_json,
	"gradient": {
		"colors": [
			"#ff6666ff",
			"#ffe766ff",
			"#8ec843ff"
		],
		"minValue": 0,
		"maxValue": 100
	},
	"legendItems": [],
	"metadata": [],
	"links": [],
	"showTacticRowBackground": False,
	"tacticRowBackground": "#dddddd",
	"selectTechniquesAcrossTactics": True,
	"selectSubtechniquesWithParent": False
}

technique_json_final = json.dumps(export_json)
write_json_to_file(technique_json_final)
## DEBUG
#print(technique_json_final)
