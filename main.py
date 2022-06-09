# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


#Service Account: mssql-restore-test@ti-is-devenv-01.iam.gserviceaccount.com
#SET GOOGLE_APPLICATION_CREDENTIALS=C:\PHome\GCPSQLAutoIn\ti-dba-automate.json

# Import the necessary packages
#from consolemenu import *
#from consolemenu.items import *
import argparse
from googleapiclient.discovery import build
from google.auth import compute_engine
import pandas as pd
import modules
from modules import *
import storage
from storage import *

import datetime
import logging
import os
import sys
import io

logger = logging.getLogger()
project = ""
projects = []
instances = []

def CloudSQLRestore(event,context):
    #Pub/Sub Message

    variables = get_variables_dynamic(event)

    computer = build('cloudresourcemanager', 'v1')
    projects = list_projects(computer)

    instances = []

    for project in projects:
        instances = instances + cloudsqlinstances(project['NAME'])

    #Preparing Instances metadata to be able to run some validations
    SourceInstanceSupplied = 0
    TargetInstanceSupplied = 0
    SourceInstance = {}
    TargetInstance = {}
    for instance in instances:
        if (variables['SourceInstance'] == instance['instance']) and SourceInstanceSupplied != 1:
            if (variables['SourceProject'] == instance['project']):
                SourceInstance = instance
                SourceInstanceSupplied = 1
        if (variables['TargetInstance'] == instance['instance']) and TargetInstanceSupplied != 1:
            if (variables['TargetProject'] == instance['project']):
                TargetInstance = instance
                TargetInstanceSupplied = 1

    #restoreinstance(SourceInstance,TargetInstance,variables)

    listallbackups(SourceInstance,TargetInstance,variables)

    #logger.warning(backup)
    #logger.warning(position)

def listallbackups(SourceInstance,TargetInstance,variables):
    cloudsql = build('sqladmin','v1beta4')

    InstanceBackups = list_sql_instance_backups(cloudsql,variables)
    logger.warning(InstanceBackups)

def restoreinstance(SourceInstance,TargetInstance,variables):
    if SourceInstance['version'] == TargetInstance['version']:
        if SourceInstance['DiskGb'] <= TargetInstance['DiskGb']:
            if skipInstance(TargetInstance) == 0:
                if TargetInstance['master'] == 'N/A':
                    if TargetInstance['replica'] == 'N/A':
                        logger.warning("Restoring...")

                        instances_restore_backup_request_body = {
                            "restoreBackupContext": {
                                "kind": "sql#restoreBackupContext",
                                "backupRunId": variables['backupRunId'],
                                "instanceId": variables['SourceInstance'],
                                "project": variables['SourceProject']
                            }
                        }

                        # Construct the service object for the interacting with the Cloud SQL Admin API.
                        cloudsql = build('sqladmin','v1beta4')
                        request = cloudsql.instances().restoreBackup(project=variables['TargetProject'], instance=variables['TargetInstance'], body=instances_restore_backup_request_body)
                        response = request.execute()

                        # TODO: Change code below to process the `response` dict:
                        logger.warning(response)

                    else:
                        logger.warning("Target Replication replica")
                else:
                    logger.warning("Target Replication master")
            else:
                logger.warning("Target not Running")
        else:
            logger.warning("Target Storage not enought")
    else:
        logger.warning("Target Storage different version")


def cloudsqlinstances(proj):
    # Construct the service object for the interacting with the Cloud SQL Admin API.
    #print(proj)
    cloudsql = build('sqladmin','v1beta4')
    if not proj:
        computer = build('cloudresourcemanager', 'v1')
        projects = list_projects(computer)
        for project in projects:
            instances = list_sql_instances(cloudsql, project["NAME"])
    else:
        instances = list_sql_instances(cloudsql, proj)

    return instances

def cloudsqldatabases(instances):
    # Construct the service object for the interacting with the Cloud SQL Admin API.
    cloudsql = build('sqladmin','v1beta4')

    databases = []
    if not instances:
        computer = build('cloudresourcemanager', 'v1')
        projects = list_projects(computer)
        for project in projects:
            instances = list_sql_instances(cloudsql, project["name"])

    if instances:
        for instance in instances:
            databases = databases + list_sql_instance_databases(cloudsql,instance['project'],instance['instance'])
    else:
        databases=["Empty"]

    return databases

def cloudsqlusers(instances):

    # Construct the service object for the interacting with the Cloud SQL Admin API.
    cloudsql = build('sqladmin','v1beta4')

    users = []
    for instance in instances:
        users = users + list_sql_instance_users(cloudsql,instance['project'],instance['instance'])

    return users

def cloudsqldatabases2(instances):

    # Construct the service object for the interacting with the Cloud SQL Admin API.
    cloudsql = build('sqladmin','v1beta4')

    databases = []

    if instances:
        for instance in instances:
            if skipInstance(instance) == 0:
                databases = databases + list_sql_databases(cloudsql,instance)
    else:
        databases=["Empty"]

    return databases

def my_quit_fn():
   raise SystemExit

def invalid():
   print ("INVALID CHOICE!")
