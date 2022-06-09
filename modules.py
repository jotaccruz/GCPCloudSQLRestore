from pprint import pprint
from googleapiclient.errors import HttpError
import dbDriver
from dbDriver import *
import json
from glom import glom
from glom import SKIP
import credential
from credential import *
import logging
import ast

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
        eventdata = event['data']

        if 'SourceProject' in eventdata:
            variables['SourceProject'] = eventdata['SourceProject']
        if 'SourceInstance' in eventdata:
            variables['SourceInstance'] = eventdata['SourceInstance']
        if 'TargetProject' in eventdata:
            variables['TargetProject'] = eventdata['TargetProject']
        if 'TargetInstance' in eventdata:
            variables['TargetInstance'] = eventdata['TargetInstance']
        if 'CreateOnFlight' in eventdata:
            variables['CreateOnFlight'] = eventdata['CreateOnFlight']
        if 'backupRunId' in eventdata:
            variables['backupRunId'] = eventdata['backupRunId']
        if 'BackupDate' in eventdata:
            variables['BackupDate'] = eventdata['BackupDate']
        if 'Level' in eventdata:
            variables['Level'] = eventdata['Level']


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

def get_database(variables):
    fields = ast.literal_eval(variables['query'][0][1])

    database = []
    if variables["type"]=='mysql':
        db = None
        db = db or init_connection_engine(variables)
        with db.connect() as conn:
            stmt = sqlalchemy.text(
                variables['query'][0][0]
            )
            # Execute the query and fetch all results
            entity_query = conn.execute(stmt).fetchall()
            # Convert the results into a list of dicts representing databases
            for row in entity_query:
                sqlDatabase = {}
                sqlDatabase['project'] = variables["project"]
                sqlDatabase['instance'] = variables["instanceName"]
                for field in range(0,len(fields)):
                    sqlDatabase[fields[field]] = row[fields[field]]
                database.append(sqlDatabase)
    else:
        for db in variables["db_list"]:
            variables["db_name"] = db["database"]
            if variables["db_name"] != 'master' and variables["db_name"] != 'model' and variables["db_name"] != 'msdb' and variables["db_name"] != 'tempdb':
                db = None
                db = db or init_connection_engine(variables)

                with db.connect() as conn:
                    stmt = sqlalchemy.text(
                        variables['query'][0][0]
                    )
                    # Execute the query and fetch all results
                    entity_query = conn.execute(stmt).fetchall()
                    # Convert the results into a list of dicts representing databases
                    for row in entity_query:
                        sqlDatabase = {}
                        sqlDatabase['project'] = variables["project"]
                        sqlDatabase['instance'] = variables["instanceName"]
                        sqlDatabase['TABLE_SCHEMA'] = variables["db_name"]
                        for field in range(0,len(fields)):
                            sqlDatabase[fields[field]] = row[fields[field]]
                        database.append(sqlDatabase)
    return database

# [START list_sql_instance_users]
def list_sql_instance_users(cloudsql,projectName,instanceName):
    sqlUsers = []
    try:
        if instanceName=='na':
            req = cloudsql.users().list(project=projectName)

        else:
            req = cloudsql.users().list(project=projectName,instance=instanceName)

        resp = req.execute()

        if 'error' not in resp:
            variables = get_variables()
            users_fields = get_entity_fields(variables,"cloudsql_users")
            for users in resp['items']:
                sqlUser = {}
                #if databases['name'] not in ['sys','mysql','information_schema','performance_schema']:
                #print(instances)
                for key in users_fields:
                    sqlUser[key[3]] = glom(users,key[1],default='N/A')
                sqlUsers.append(sqlUser)
    except Exception as error:
        variables = get_variables()
        users_fields = get_entity_fields(variables,"cloudsql_users")
        sqlUser = {}
        for key in users_fields:
            sqlUser[key[3]] = 'N/A'
        sqlUsers.append(sqlUser)
        return sqlUsers
    return sqlUsers
# [END list_sql_instance_users]

# [START list_sql_instance_users]
def list_sql_instance_grants(cloudsql,projectName,instanceName):
    sqlUsers = []
    try:
        if instanceName=='na':
            req = cloudsql.users().list(project=projectName)

        else:
            req = cloudsql.users().list(project=projectName,instance=instanceName)

        resp = req.execute()

        if 'error' not in resp:
            users_fields = get_entity_fields("cloudsql_users")
            for users in resp['items']:
                sqlUser = {}
                #if databases['name'] not in ['sys','mysql','information_schema','performance_schema']:
                #print(instances)
                for key in users_fields:
                    sqlUser[key[3]] = glom(users,key[1],default='N/A')
                sqlUsers.append(sqlUser)
    except Exception as error:
        databases_fields = get_entity_fields("cloudsql_users")
        sqlUser = {}
        for key in databases_fields:
            sqlUser[key[3]] = 'N/A'
        sqlUsers.append(sqlUser)
        return sqlUsers
    return sqlUsers
# [END list_sql_instance_users]

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


# [START wait_for_operation]
def wait_for_operation(cloudsql, project, operation):
    print('Waiting for operation to finish...')
    while True:
        result = cloudsql.operations().get(
            project=project,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result
        time.sleep(1)
# [END wait_for_operation]
# wait_for_operation(cloudsql, "ti-is-devenv-01", operation)

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


# [START list_sql_instance_backups]
def list_sql_instance_backups(cloudsql,variable):
    InstanceBackups = []
    try:
        request = cloudsql.backupRuns().list(project=variable['SourceProject'], instance=variable['SourceInstance'])
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
