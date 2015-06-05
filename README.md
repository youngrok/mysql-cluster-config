# mysql-cluster-config

AUTOMATED MYSQL CLUSTER INSTALLATION ON UBUNTU USING FABRIC

## Prerequisite

	pip install -r requirements


create servers.py in project root folder:

    from fabric.state import env
    
    env.servers = {
        'mgm_nodes': [
            ('external ip', 'internal ip', 'root password'),
        ],
        'data_nodes': [
            ('external ip', 'internal ip', 'root password'),
        ],
        'sql_nodes': [
            ('external ip', 'internal ip', 'root password'),
        ],
    }
	
## Usage

	fab setup_mgm_nodes
	fab setup_data_nodes
	fab setup_sql_nodes

## setup newrelic

    fab newrelic:LICENSE_KEY
    
## Connect
connect on sql node server.

	mysql -uroot

## Caution
when create table, specify ENGINE=NDB

example.

    DROP TABLE IF EXISTS `City`;
    CREATE TABLE `City` (
      `ID` int(11) NOT NULL auto_increment,
      `Name` char(35) NOT NULL default '',
      `CountryCode` char(3) NOT NULL default '',
      `District` char(20) NOT NULL default '',
      `Population` int(11) NOT NULL default '0',
      PRIMARY KEY  (`ID`)
    ) ENGINE=NDBCLUSTER DEFAULT CHARSET=latin1;
    
    INSERT INTO `City` VALUES (1,'Kabul','AFG','Kabol',1780000);
    INSERT INTO `City` VALUES (2,'Qandahar','AFG','Qandahar',237500);
    INSERT INTO `City` VALUES (3,'Herat','AFG','Herat',186800);

