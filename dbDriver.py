# -*- coding: utf-8 -*-
"""
Python 3.8
@author: juan.cruz2

"""
import sqlalchemy
import os
import logging
import pyodbc
import sqlalchemy_pytds

logger = logging.getLogger()

def init_connection_engine(variables):
    #print(ServiceT)
    db_config = {
        # [START cloud_sql_mysql_sqlalchemy_limit]
        # Pool size is the maximum number of permanent connections to keep.
        "pool_size": 5,
        # Temporarily exceeds the set pool_size if no connections are available.
        "max_overflow": 2,
        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.
        # [END cloud_sql_mysql_sqlalchemy_limit]

        # [START cloud_sql_mysql_sqlalchemy_backoff]
        # SQLAlchemy automatically uses delays between failed connection attempts,
        # but provides no arguments for configuration.
        # [END cloud_sql_mysql_sqlalchemy_backoff]

        # [START cloud_sql_mysql_sqlalchemy_timeout]
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        "pool_timeout": 30,  # 30 seconds
        # [END cloud_sql_mysql_sqlalchemy_timeout]

        # [START cloud_sql_mysql_sqlalchemy_lifetime]
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # reestablished
        "pool_recycle": 1800,  # 30 minutes
        # [END cloud_sql_mysql_sqlalchemy_lifetime]

    }

    if os.environ.get("DB_HOST"):
        return init_tcp_connection_engine(db_config,variables)
    else:
        if variables["type"]=='mssql':
            return tcp_connection_engine(db_config,variables)
        else:
            return init_unix_connection_engine(db_config,variables)


def init_tcp_connection_engine(db_config,variables):
    # [START cloud_sql_mysql_sqlalchemy_create_tcp]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.
    db_user = os.environ["DB_USER"]
    db_pass = variables["credential"].token#os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_host = os.environ["DB_HOST"]

    # Extract host and port from db_host
    host_args = db_host.split(":")
    db_hostname, db_port = host_args[0], int(host_args[1])

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            host=db_hostname,  # e.g. "127.0.0.1"
            port=db_port,  # e.g. 3306
            database=db_name,  # e.g. "my-database-name"
        ),
        **db_config
    )

    # [END cloud_sql_mysql_sqlalchemy_create_tcp]

    return pool


def init_unix_connection_engine(db_config,variables):
    # [START cloud_sql_mysql_sqlalchemy_create_socket]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
        sqlalchemy.engine.url.URL.create(
            drivername = variables["drivername"],
            username = variables["db_user"],  # e.g. "my-database-user"
            password = variables["credential"].token,  # e.g. "my-database-password"
            database = variables["db_name"],  # e.g. "my-database-name"
            query = variables["connectionstring"]
        ),
        **db_config
    )
    # [END cloud_sql_mysql_sqlalchemy_create_socket]

    return pool

def tcp_connection_engine(db_config,variables):
    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL.create(
            drivername = variables["drivername"],
            username = variables["db_user"],  # e.g. "my-database-user"
            password = variables["pwd"],  # e.g. "my-database-password"
            database = variables["db_name"],  # e.g. "my-database-name"
            host = variables["host"],
            port = variables["port"],
            #query = variables["connectionstring"]
        ),
        **db_config
    )

    # [END cloud_sql_mysql_sqlalchemy_create_tcp]

    return pool
