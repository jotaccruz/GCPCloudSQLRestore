#set GOOGLE_APPLICATION_CREDENTIALS=C:\PHome\GCPSQLAutoIn\cloudsqlproxy.json

from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
#from google.oauth2 import service_account
import google.auth

#JC2 modification to https://developers.google.com/people/quickstart/python

def mycredential():
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/sqlservice.admin']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    credentials, project = google.auth.default(scopes=SCOPES)
    auth_req = Request()
    credentials.refresh(auth_req)

    #with open('token.json', 'w') as token:
    #    token.write(credentials.token)

    return credentials
