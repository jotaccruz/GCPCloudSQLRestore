from pprint import pprint
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

import dbDriver
from dbDriver import *
import json
from glom import glom
from glom import SKIP
import credential
from credential import *
import logging
import ast
import base64
import random
import string
import time

# This global variable is declared with a value of `None`, instead of calling
# `init_connection_engine()` immediately, to simplify testing. In general, it
# is safe to initialize your database connection pool when your script starts
# -- there is no need to wait for the first request.
db = None
# [START list_projects]
# Permissions required: resourcemanager.projects.get
logger = logging.getLogger()

def get_variables():
    mycredentials = mycredential()

    variables = {}

    variables["credential"] = mycredentials
    variables['type'] = 'mysql'
    variables['drivername'] = 'mysql+pymysql'
    variables["db_user"] = os.environ["DB_USER"]
    #variables["db_pass"] = ServiceT#os.environ["DB_PASS"]
    variables["db_name"] = os.environ["DB_NAME"]
    variables["cloud_sql_connection_name"] = os.environ["CLOUD_SQL_CONNECTION_NAME"]
    variables["db_socket_dir"] = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    variables["connectionstring"]={
        "unix_socket": "{}/{}".format(
            variables["db_socket_dir"],  # e.g. "/cloudsql"
            variables["cloud_sql_connection_name"])  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
    }
    return variables


def get_variables_dynamic(event):

    mycredentials = mycredential()

    variables = {}
    variables['credential'] = mycredentials

    if 'data' in event:
        event = base64.b64decode(event['data']).decode('utf-8')
        eventjson = json.loads(event)
        eventdata = eventjson['data']

        if 'SourceProject' in eventdata:
            variables['SourceProject'] = eventdata['SourceProject']
        if 'SourceInstance' in eventdata:
            variables['SourceInstance'] = eventdata['SourceInstance']
        if 'TargetProject' in eventdata:
            variables['TargetProject'] = eventdata['TargetProject']
        if 'TargetInstance' in eventdata:
            variables['TargetInstance'] = eventdata['TargetInstance']
        if 'backupRunId' in eventdata:
            variables['backupRunId'] = eventdata['backupRunId']
    return variables


def list_projects(compute):
    request = compute.projects().list()
    response = request.execute()
    projects = []

    #print (response)
    for project in response.get('projects', []):
        # TODO: Change code below to process each `project` resource:
        proj = {}
        proj['NAME'] = project['name']

        projects.append(proj)
    return projects
# [END list_projects]

def get_entity_fields(variables,pentity):
    global db

    db = db or init_connection_engine(variables)

    fields = []
    with db.connect() as conn:
        stmt = sqlalchemy.text(
            "SELECT entity, keyaddress, keyname, keyalias FROM metadataapi WHERE entity=:entity AND status=1 ORDER BY orderlist ASC"
        )
        # Execute the query and fetch all results
        entity_fields = conn.execute(stmt,entity=pentity).fetchall()
        # Convert the results into a list of dicts representing votes
        for row in entity_fields:
            fields.append(row)
    return fields

# [START list_sql_instances]
def list_sql_instances(cloudsql,projectname):
    req = cloudsql.instances().list(project=projectname)
    resp = req.execute()
    #print(glom(resp['items'][1],'name'))

    if 'error' not in resp:
        sqlinstances = []
        variables = get_variables()
        cloudsql_fields = get_entity_fields(variables,"cloudsql")
        for instances in resp['items']:
            sqlinstance = {}
            #print(instances)
            for key in cloudsql_fields:
                sqlinstance[key[3]] = glom(instances,key[1],default='N/A')
            sqlinstances.append(sqlinstance)

    return sqlinstances
# [END list_sql_instances]

def skipInstance(instance):
    if 'activationPolicy' in instance:
        if instance['activationPolicy'] != "NEVER":
            return 0
        else:
            return 1

# [START list_sql_instance_backups]
def list_sql_instance_backups(cloudsql,SourceInstance):
    InstanceBackups = []
    try:
        request = cloudsql.backupRuns().list(project=SourceInstance['project'], instance=SourceInstance['instance'])
        response = request.execute()

        if 'error' not in response:
            variables = get_variables()
            backups_fields = get_entity_fields(variables,"cloudsql_backups")
            for backups in response['items']:
                InstanceBackup = {}
                #if databases['name'] not in ['sys','mysql','information_schema','performance_schema']:
                #print(instances)
                for key in backups_fields:
                    InstanceBackup[key[3]] = glom(backups,key[1],default='N/A')
                InstanceBackups.append(InstanceBackup)
    except Exception as error:
        variables = get_variables()
        databases_fields = get_entity_fields(variables,"cloudsql_backups")
        InstanceBackup = {}
        for key in databases_fields:
            InstanceBackup[key[3]] = 'N/A'
        InstanceBackups.append(InstanceBackup)
        return InstanceBackups
    return InstanceBackups
# [END list_sql_instance_backups]

# [START list_sql_instance_databases]
def list_sql_instance_databases(cloudsql,projectName='na',instanceName='na'):
    sqlDatabases = []
    try:
        if instanceName=='na':
            req = cloudsql.databases().list(project=projectName)
        else:
            req = cloudsql.databases().list(project=projectName,instance=instanceName)

        resp = req.execute()

        if 'error' not in resp:
            variables = get_variables()
            databases_fields = get_entity_fields(variables,"cloudsql_databases")
            for databases in resp['items']:
                sqlDatabase = {}
                #if databases['name'] not in ['sys','mysql','information_schema','performance_schema']:
                #print(instances)
                for key in databases_fields:
                    sqlDatabase[key[3]] = glom(databases,key[1],default='N/A')
                sqlDatabases.append(sqlDatabase)
    except Exception as error:
        variables = get_variables()
        databases_fields = get_entity_fields(variables,"cloudsql_databases")
        sqlDatabase = {}
        for key in databases_fields:
            sqlDatabase[key[3]] = 'N/A'
        sqlDatabases.append(sqlDatabase)
        return sqlDatabases
    return sqlDatabases
# [END list_sql_instance_databases]

def get_entity_query(variables):
    global db
    db = db or init_connection_engine(variables)

    query = []
    with db.connect() as conn:
        stmt = sqlalchemy.text(
            "SELECT query,fields FROM metadatadb WHERE entity=:entity and status = 1"
        )
        # Execute the query and fetch all results
        entity_query = conn.execute(stmt,entity=variables['type']).fetchall()
        # Convert the results into a list of dicts representing votes
        for row in entity_query:
            query.append(row)
    return query

# [START getFileUrl]
def getFileUrl(filename,directory):
        if getattr(sys, 'frozen', False): # Running as compiled
            running_dir = sys._MEIPASS + "/" + directory + "/" #"/files/" # Same path name than pyinstaller option
        else:
            running_dir = "./" + directory + "/" # Path name when run with Python interpreter
        FileName = running_dir + filename #"moldmydb.png"
        return FileName
# [END getFileUrl]

# [START readFileFromOS]
def readFileFromOS(filename):
    with open(filename,'r') as file:
        data=file.read()
    return data
# [END readFileFromOS]

def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


# [START destroy_sqlinstance]
def destroy_sqlinstance(projectname,sqlinstance_name):
    cloudsql = build('sqladmin','v1beta4')
    return cloudsql.instances().delete(project=projectname,instance=sqlinstance_name).execute()
# [END destroy_sqlinstance]
# destroy_sqlinstances(cloudsql,"ti-is-devenv-01","sql1")


# [START wait_for_operation]
def wait_for_operation(project, operation):
    cloudsql = build('sqladmin','v1beta4')
    logger.warning('Waiting for operation to finish...')
    while True:
        result = cloudsql.operations().get(
            project=project,
            operation=operation).execute()

        if result['status'] == 'DONE':
            logging.warning("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result
        time.sleep(1)
# [END wait_for_operation]
# wait_for_operation(cloudsql, "ti-is-devenv-01", operation)


# [START get_random_string]
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
# [END get_random_string]
# get_random_string(6)


# [START generate_random_name]
def generate_random_name(sqlinstance_name,length):
	sqlinstance_name = sqlinstance_name + "-" + get_random_string(length)
	return sqlinstance_name
# [END generate_random_name]
# generate_random_name("prefix",6)


# [START create_instance]
def create_sqlinstance(project, zone, sqlinstance_name, machine_type, ssd_size, sqlversion, saPasswd):
    # Configure the SQL Instance
    cloudsql = build('sqladmin','v1beta4')
    regions = zone.rfind('-',0,2)-1
    config = {
        'name': sqlinstance_name,
        'gceZone': zone,
        'region': zone[0:regions],
        'databaseVersion': sqlversion,
        'rootPassword': saPasswd,
        'settings': {
            'locationPreference':{
                'zone': zone
            },
            'userLabels': {
                'owner': 'dba',
                'purpose': 'restore_test_automation'
            },
            'tier': machine_type,
            'dataDiskSizeGb': ssd_size,
            'ipConfiguration': {
                'authorizedNetworks': [
                    {
                        'value': '208.181.137.109',
                        #"expirationTime": '2021-10-02T15:01:23Z',
                        'name': 'VDI'
                    }
                ]
            },
        },
    }
    return cloudsql.instances().insert(
        project=project,
        body=config).execute()
# [END create_instance]
# create_sqlinstance(cloudsql,"ti-is-devenv-01","us-west1-a",generate_random_name(5),"db-custom-4-15360",100,'SQLSERVER_2017_WEB',"Pass12345")


# [START import_instance]
def import_sqlinstance(project, sqlinstance_name,database_name,filetype):
    cloudsql = build('sqladmin','v1beta4')
    config = {
        'importContext': {
            'uri': 'gs://dba-freenas/SUSWEYAK15_EvoDb_Testing_FULL_20200325_011850.bak',
            'database': database_name,
            'fileType': filetype
        }
    }

    return cloudsql.instances().import_(
    	project=project,
    	instance=sqlinstance_name,
    	body=config).execute()
# [END import_instance]
# import_sqlinstance(cloudsql,"ti-is-devenv-01","us-west1-a",instances['targetID'],'EvoDb_Testing','BAK')


# [START generate_random_name]
def generate_random_name(sqlinstance_name,length):
    sqlinstance_name = sqlinstance_name + "-" + get_random_string(length)
    return sqlinstance_name
# [END generate_random_name]
# generate_random_name("prefix",6)
