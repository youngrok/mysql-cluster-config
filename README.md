# fabric-mysql-cluster

AUTOMATED MYSQL CLUSTER INSTALLATION ON UBUNTU USING FABRIC

## Prerequisite

##### fabric

`pip install fabric`


## Usage

### set roles

hosts: The hosts used for the ssh connection. This is also used for the cluster establishment if node_hosts are empty or not defined.

[optional] node_hosts: The hosts used for the cluster establishment. This is used when the hosts for ssh connection are different from the hosts for cluster establishment.

```
env.roledefs = { 
    'mgm_nodes': {
        'hosts': ['116.34.66.1'],
        'node_hosts': ['10.211.55.1']
    },
    'data_nodes': {
        'hosts': ['116.34.66.2', '116.34.66.3'],
        'node_hosts': ['10.211.55.2', '10.211.55.3']
    },
    'sql_nodes': {
        'hosts': ['116.34.66.4'],
        'node_hosts': ['10.211.55.4']
    }
}
```

##### [optional] set passwords

```
env.passwords = {
    'root@116.34.66.1:22': '<password>',
    'root@116.34.66.2:22': '<password>',
    'root@116.34.66.3:22': '<password>',
    'root@116.34.66.4:22': '<password>',
}
```

### setup mysql cluster

`fab setup_mysql_cluster`



##### setup individual nodes


setup management nodes

`fab setup_mgm_nodes`

setup data nodes

`fab setup_data_nodes`

setup sql nodes

`fab setup_sql_nodes`

### start mysql cluster

`fab start_mysql_cluster`

##### start individual nodes


start management nodes

`fab start_mgm_nodes`

start data nodes

`fab start_data_nodes`

start sql nodes

`fab start_sql_nodes`

###test mysql cluster

##### local connection to mysql cluter (sql node)

```
mysql -u root

mysql> create database clustertest;
Query OK, 1 row affected (0.11 sec)

mysql> use clustertest;
Database changed

mysql> create table testtable (i int) engine=ndbcluster;
Query OK, 0 rows affected (0.26 sec)

mysql> insert into testtable () values (1122334455);
Query OK, 1 row affected (0.00 sec)

mysql> select * from testtable;
+------------+
| i          |
+------------+
| 1122334455 |
+------------+
1 row in set (0.00 sec)
```

try to disconnect some data nodes (not all data nodes)

see if you still get the same result.

```
mysql> select * from testtable;
+------------+
| i          |
+------------+
| 1122334455 |
+------------+
1 row in set (0.00 sec)
```

##### for non-local connections

grand access to all hosts

`mysql> GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'password' WITH GRANT OPTION;`

connect mysql outside sql node

`mysql -h sql_node_host -u root`
