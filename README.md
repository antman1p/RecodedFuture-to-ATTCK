# Recorded Future Export to JSON Scripts
Use these scripts to convert CSV data exported from Recorded Future to import into various applications such as ATT&CK Navigator and Vectr
## Usage
###### General
1. Export APT date from Recorded Future to CSV
2. Edit the `sample.env` file
    1. Make sure the CSV path and CSV filename match the location and name of the exported CSV file
    2. Add your Vectr API Key ID and Secret Key seperated by a : `API_KEY="API_KEY_ID:SECRET_KEY"` 
    3. Change your ORG_NAME and ASSESSMENT_NAME to the organization and assessment you created manually in vectr
3. Install dependencies: `pip install -r requirements.txt`

###### RFtoAttackNav.py
This script takes CSV data exported by Recorded Future and outputs the JSON document needed by ATT&CK Navigator for importing a new layer
1. Follow the General steps above
2. Run `python RFtoAttackNav.py`
3. Use a web browser to navigate to https://mitre-attack.github.io/attack-navigator/
4. Import the json file as a new layer
5. Have fun manually selecting, disabling, and removing from view the unused techniques and sub-techniques

###### RFtoVectr.py
This script takes CSV data exported from Recorded Future and uses the Vectr API to create a new campaign in an asessment (defined in the .env file), creates testcases, and populated the newly created campaign with the new test cases
1. Follow the General Steps Above
2. Run `python RFtoVectr.py`
