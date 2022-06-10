USE cloudsqlcollector

CREATE TABLE metadataapi (  entity VARCHAR(250),  keyaddress VARCHAR(500),  keyname VARCHAR(250),  keyalias VARCHAR(250),  status INT,  orderlist INT)

--SELECT entity, keyaddress, keyname, keyalias FROM metadataapi WHERE entity=:entity AND status=1 ORDER BY orderlist ASC

INSERT INTO metadataapi VALUES ('cloudsql','project','project','project',1,1);
INSERT INTO metadataapi VALUES ('cloudsql','name','name','instance',1,2);
INSERT INTO metadataapi VALUES ('cloudsql','databaseVersion','databaseVersion','version',1,3);
INSERT INTO metadataapi VALUES ('cloudsql','region','region','region',1,4);
INSERT INTO metadataapi VALUES ('cloudsql','ipAddresses.0.ipAddress','ipAddress','ip',1,5);
INSERT INTO metadataapi VALUES ('cloudsql','ipAddresses.0.type','type','ip_type',1,6);
INSERT INTO metadataapi VALUES ('cloudsql','ipAddresses.1.ipAddress','ipAddress','ip2',1,7);
INSERT INTO metadataapi VALUES ('cloudsql','ipAddresses.1.type','type','ip2_type',1,8);
INSERT INTO metadataapi VALUES ('cloudsql','connectionName','connectionName','connectionName',1,9);
INSERT INTO metadataapi VALUES ('cloudsql','settings.activationPolicy','activationPolicy','activationPolicy',1,10);
INSERT INTO metadataapi VALUES ('cloudsql','settings.dataDiskSizeGb','dataDiskSizeGb','DiskGb',1,11);
INSERT INTO metadataapi VALUES ('cloudsql','masterInstanceName','masterInstanceName','master',1,12);
INSERT INTO metadataapi VALUES ('cloudsql','replicaNames.0','replicaNames','replica',1,13);


INSERT INTO metadataapi VALUES ('cloudsql_databases','project','project','project',1,7);
INSERT INTO metadataapi VALUES ('cloudsql_databases','instance','instance','instance',1,8);
INSERT INTO metadataapi VALUES ('cloudsql_databases','name','name','database',1,9);

INSERT INTO metadataapi VALUES ('cloudsql_users','project','project','project',1,10);
INSERT INTO metadataapi VALUES ('cloudsql_users','instance','instance','instance',1,11);
INSERT INTO metadataapi VALUES ('cloudsql_users','name','name','user',1,12);
INSERT INTO metadataapi VALUES ('cloudsql_users','host','host','host',1,13);

INSERT INTO metadataapi VALUES ('cloudsql_backups','id','id','id',1,1);
INSERT INTO metadataapi VALUES ('cloudsql_backups','status','status','status',1,2);
INSERT INTO metadataapi VALUES ('cloudsql_backups','startTime','startTime','startTime',1,3);
INSERT INTO metadataapi VALUES ('cloudsql_backups','endTime','endTime','endTime',1,4);


CREATE TABLE metadatadb ( entity VARCHAR(250),  query VARCHAR(600), fields VARCHAR(250), status INT);
INSERT INTO metadatadb VALUES ('mysql', "SELECT TABLE_SCHEMA, TABLE_NAME, IFNULL(ROUND((data_length + index_length) / 1024 / 1024, 1),0) 'MB', IFNULL(DATE_FORMAT(CREATE_TIME,'%d/%m/%y'),'01/01/05') CREATE_TIME, IFNULL(DATE_FORMAT(UPDATE_TIME,'%d/%m/%y'),'01/01/05') UPDATE_TIME FROM information_schema.tables WHERE TABLE_SCHEMA NOT IN ('mysql','sys','information_schema','performance_schema')", "['TABLE_SCHEMA','TABLE_NAME','MB','CREATE_TIME','UPDATE_TIME']",1);
INSERT INTO metadatadb VALUES ('postgresql', "select tablename AS ""TABLE_NAME"", (pg_relation_size("'''"'''"||schemaname||"'''"."'''"||tablename||"'''"'''"))/1024/1024 AS ""MB"", to_char(DATE '1999-01-01', 'DD/MM/YY') AS ""CREATE_TIME"", to_char(DATE '1999-01-01', 'DD/MM/YY') AS ""UPDATE_TIME"" from pg_catalog.pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')","['TABLE_NAME','MB','CREATE_TIME','UPDATE_TIME']",1);
INSERT INTO metadatadb VALUES ('mssql', "SELECT db_name() AS TABLE_SCHEMA, t.Name AS TABLE_NAME, CAST(ROUND((SUM(a.used_pages) / 128.00), 2) AS NUMERIC(36, 2)) AS MB, t.create_date AS CREATE_TIME, t.modify_date AS UPDATE_TIME FROM sys.tables t INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id GROUP BY t.Name, s.Name, t.create_date, t.modify_date ORDER BY s.Name, t.Name, t.create_date, t.modify_date","['TABLE_SCHEMA','TABLE_NAME','MB','CREATE_TIME','UPDATE_TIME']",1);


INSERT INTO metadatadb VALUES ('mssql', "EXEC sp_MSforeachdb 'IF ''?'' NOT IN(''master'', ''model'', ''msdb'', ''tempdb'') BEGIN USE ? SELECT db_name() AS TABLE_SCHEMA, t.Name AS TABLE_NAME, CAST(ROUND((SUM(a.used_pages) / 128.00), 2) AS NUMERIC(36, 2)) AS MB, t.create_date AS CREATE_TIME, t.modify_date AS UPDATE_TIME FROM sys.tables t INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id GROUP BY t.Name, s.Name, t.create_date, t.modify_date ORDER BY s.Name, t.Name, t.create_date, t.modify_date END';","['TABLE_NAME','MB','CREATE_TIME','UPDATE_TIME']",1);

SELECT query,fields FROM metadatadb WHERE status = 1

INSERT INTO metadatadb VALUES ('postgresql', "select schemaname AS ""TABLE_SCHEMA"", tablename AS ""TABLE_NAME"", (pg_relation_size("'''"'''"||schemaname||"'''"."'''"||tablename||"'''"'''"))/1024/1024 AS ""MB"", to_char(DATE '1999-01-01', 'DD/MM/YY') AS ""CREATE_TIME"", to_char(DATE '1999-01-01', 'DD/MM/YY') AS ""UPDATE_TIME"" from pg_catalog.pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')","['TABLE_SCHEMA','TABLE_NAME','MB','CREATE_TIME','UPDATE_TIME']",1);

/*select
schemaname AS "TABLE_SCHEMA",
tablename AS "TABLE_NAME",
(pg_relation_size('"'||schemaname||'"."'||tablename||'"'))/1024/1024 AS "MB",
to_char(DATE '1999-01-01', 'DD/MM/YY') AS "CREATE_TIME",
to_char(DATE '1999-01-01', 'DD/MM/YY') AS "UPDATE_TIME"
from
pg_catalog.pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')
*/
