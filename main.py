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

    #Preparing Source and Target Instance smetadata to be able to run some validations

    computer = build('cloudresourcemanager', 'v1')
    projects = list_projects(computer)

    instances = []

    for project in projects:
        instances = instances + cloudsqlinstances(project['NAME'])

    if 'backupRunId' in variables:
        SourceInstance = sinstance(instances,variables)
        TargetInstance = tinstance(instances,variables)
        if SourceInstance:
            if TargetInstance:
                restoreinstance(SourceInstance,TargetInstance,variables)
            else:
                logger.warning("Creating the Target CloudSQL Instance...")

                operation = create_sqlinstance(variables['TargetProject'],SourceInstance['zone'],generate_random_name(variables['TargetInstance'],5),SourceInstance['tier'],SourceInstance['DiskGb'],SourceInstance['version'],"Pass12345")
                wait_for_operation(variables['TargetProject'], operation['name'])
                variables['TargetInstance'] = operation['targetId']

                print("""
            CloudSQL Instance {} created.
            It will take a minute or two for the instance to complete work.
            """.format(operation['targetId']))
                for project in projects:
                    instances = instances + cloudsqlinstances(project['NAME'])
                TargetInstance = tinstance(instances,variables)
                restoreinstance(SourceInstance,TargetInstance,variables)
        else:
            logger.warning("All the necessary metadata not supplied")
    else:
        SourceInstance = sinstance(instances,variables)
        if SourceInstance:
            listallbackups(SourceInstance)
        else:
            logger.warning("Source Instance metadata not supplied")

def sinstance(instances,variables):
    SourceInstanceSupplied = 0
    SourceInstance = {}
    for instance in instances:
        if (variables['SourceInstance'] == instance['instance']) and SourceInstanceSupplied != 1:
            if (variables['SourceProject'] == instance['project']):
                SourceInstance = instance
                SourceInstanceSupplied = 1
    return SourceInstance

def tinstance(instances,variables):
    TargetInstanceSupplied = 0
    TargetInstance = {}
    for instance in instances:
        if (variables['TargetInstance'] == instance['instance']) and TargetInstanceSupplied != 1:
            if (variables['TargetProject'] == instance['project']):
                TargetInstance = instance
                TargetInstanceSupplied = 1
    return TargetInstance

def listallbackups(SourceInstance):
    cloudsql = build('sqladmin','v1beta4')

    InstanceBackups = list_sql_instance_backups(cloudsql,SourceInstance)

    Backups = []
    for Backup in InstanceBackups:
        if Backup['status']=='SUCCESSFUL':
            Backups.append(Backup)

    Backups_df = pd.DataFrame(Backups)
    Backups_df = Backups_df.sort_values(by="startTime",ascending=False)
    b_buf = io.StringIO()
    # saving a data frame to a buffer (same as with a regular file):
    Backups_df.to_csv(b_buf)
    b_buf.seek(0)
    fname = SourceInstance['instance']+'_backups.csv'
    bucket(b_buf,fname)

    return Backups


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
                    else:
                        logger.warning("CloudSQL Target Instance Replication MASTER")
                else:
                    logger.warning("CloudSQL Target Instance Replication REPLICA")
            else:
                logger.warning("CloudSQL Target Instance not Running")
        else:
            logger.warning("CloudSQL Target Instance Storage not enought")
    else:
        logger.warning("CloudSQL Target Instance Different version")


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
