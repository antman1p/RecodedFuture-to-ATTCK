#dependencies: pip install python-dotenv gql requests requests_toolbelt pydantic beautifulsoup4
from dotenv import dotenv_values
from bs4 import BeautifulSoup
import re
import csv
import os
import requests
import sys
from gql import Client, gql
from vectr_api_client import VectrGQLConnParams, \
    create_test_cases, \
    get_client, \
    get_org_id_for_campaign_and_assessment_data
    
env_config = dotenv_values("sample.env")

def get_techniques_from_csv(csv_path):
    technqs = set()
    with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
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
    
def get_test_case_tuples(url_ready_tech_set, apt_name):
    # Tuple needs to have name ("Technique Name - APT Name"), tactic/phase name, technique number
    tuple_list = []
    mitre_technique_url ="https://attack.mitre.org/techniques/"
    for tech in url_ready_tech_set:
        url = mitre_technique_url + tech + "/"
        dot_tech = tech.replace("/", ".")
        print("[+] Scraping Mitre Page for Technique details: %s" % (url))
        sys.stdout.flush()
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        tactic = soup.find("span", attrs={"class": "h5 card-title"}, string=re.compile("(Tactic)s*(:)")).find_next_sibling("a").get_text()
        tech_name = str(soup.find("h1").get_text()).strip()
        tech_name = tech_name.replace('\n', " ")
        tech_name = " ".join(tech_name.split())
        tech_name = "%s - %s" % (tech_name, apt_name)
        tac_tech_tuple = (tech_name, dot_tech, tactic)
        tuple_list.append(tac_tech_tuple)
    print("\n[+] Finished Scraping")
    return tuple_list

def create_campaign(target_db, campaign_name, connection_params, org_id, parent_assessment_id):
    campaign_data = {
        "name": campaign_name,
        "organizationIds": [org_id]
    }
    campaign_mutation = gql(
        """
        mutation ($input: CreateCampaignInput!) {
            campaign {
                create(input: $input) {
                    campaigns {
                        id, name, description, createTime
                    }
                }
            }
        }
        """
    )
    
    campaign_vars = {
        "input": {
            "db": target_db,
            "assessmentId": parent_assessment_id,
            "campaignData": [campaign_data]
        }
    }
    vectr_client = get_client(connection_params)
    campaign_id = (vectr_client.execute(campaign_mutation, variable_values=campaign_vars))["campaign"]["create"]["campaigns"][0]["id"]
    print("\n[+] Created new Campaign: %s\n" % (campaign_name))
    return campaign_id

def create_new_testcases(test_tuple_list, org_name, target_db, campaign_id, apt_name):
    test_case_mutation = gql(
        '''
        mutation ($input: CreateTestCaseAndTemplateMatchByNameInput!) {
            testCase {
                createWithTemplateMatchByName(input: $input) {
                    testCases {
                        id, name, description, createTime
                    }
                }
            }
        }
        '''
    )
    
    
    for test_tuple in test_tuple_list:
        test_case_data = []
        tech_name = test_tuple[0]
        tech_num = test_tuple[1]
        tact_name = test_tuple[2]

        test_case_dict = {
            "name": tech_name,
            "description": " ",
            "phase": tact_name,
            "technique": tech_num,
            "organization": org_name,  
            "status": "NOTPERFORMED"
        }
        test_case_data.append({
            "testCaseData": test_case_dict
        })
        
        test_case_vars = {
            "input": {
                "db": target_db,
                "campaignId": campaign_id,
                "createTestCaseInputs": test_case_data  
            }
        }
        
        vectr_client = get_client(connection_params)
        vectr_client.execute(test_case_mutation, variable_values=test_case_vars)
        print("[+] Creating Test Case for %s - %s" % (tech_num, tech_name))
        sys.stdout.flush()
    print("\n[+] Test Case Completion Complete")
        
        

target_db = env_config.get("TARGET_DB")

techniques = get_techniques_from_csv(csv_path=env_config.get("CSV_PATH"))

url_ready_techniques = technique_to_mitre_path(techniques)

apt_name = get_apt_name(csv_path=env_config.get("CSV_PATH"))

test_tuple_list = get_test_case_tuples(url_ready_techniques, apt_name)

connection_params = VectrGQLConnParams(api_key=env_config.get("API_KEY"),
                                       vectr_gql_url=env_config.get("VECTR_GQL_URL"))


assessment_name = env_config.get("ASSESSMENT_NAME")
org_id = get_org_id_for_campaign_and_assessment_data(connection_params=connection_params, org_name=env_config.get("ORG_NAME"))

assessment_query = gql(
    """
    query($nameVar: String, $db: String!) {
      assessments(
      db: $db
      filter: {name: {eq: $nameVar}}
      first: 1
    ) {
      nodes {
        id, campaigns { id, name }
      }
    }
  }
  """
)

assessment_vars = {"nameVar": assessment_name, "db": target_db}

vectr_client = get_client(connection_params)

assessment_id = (vectr_client.execute(assessment_query, variable_values=assessment_vars))["assessments"]["nodes"][0]["id"]

campaign_name = "%s - %s" % (env_config.get("ORG_NAME"), apt_name)

new_campaign_id = create_campaign(target_db, campaign_name, connection_params, org_id, assessment_id)

create_new_testcases(test_tuple_list, env_config.get("ORG_NAME"), target_db, new_campaign_id, apt_name)

print("\n[+] Vectr Campaign and Test Cases creation complete")






    
