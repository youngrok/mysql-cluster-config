# -*- coding: utf-8 -*-
from time import sleep
from fabric.context_managers import lcd, cd, settings
from fabric.contrib.files import upload_template, exists
from fabric.decorators import roles, parallel
from fabric.operations import put, run, sudo
from fabric.state import env
from fabric.tasks import execute
from fabtools import require, fabtools
import itertools

import servers

env.roledefs = {k: [t[0] for t in env.servers[k]] for k in env.servers}
env.passwords = {'root@%s:22' % ip[0]: ip[2] for ip in itertools.chain(*env.servers.values())}

env.mysql_cluster_filename = 'mysql-cluster-gpl-7.4.6-linux-glibc2.5-x86_64.tar.gz'
env.mysql_cluster_download = 'http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.4/' + env.mysql_cluster_filename
env.mysql_home = '/usr/local/mysql'

env.user = 'root'
env.warn_only = True

def create_conf_files():
    configurations = []
    node_hosts = {}
    for node_type in ['mgm_nodes', 'data_nodes', 'sql_nodes']:
        node_hosts[node_type] = env.roledefs[node_type]['node_hosts'] if env.roledefs[node_type].get('node_hosts') else env.roledefs[node_type]['hosts']

    # configuation for config.ini
    configuration_1 = {}
    configuration_1['file'] = 'config.ini'
    configuration_1['replacements'] = {
        '<num_of_replicas>': str(len(node_hosts['data_nodes'])),
        '<mgm_node>': '',
        '<data_node>': '',
        '<sql_node>': ''
    }

    for host in node_hosts['mgm_nodes']:
        configuration_1['replacements']['<mgm_node>'] += "[ndb_mgmd]\nhostname=%s\ndatadir=/var/lib/mysql-cluster\n\n" % host

    for host in node_hosts['data_nodes']:
        configuration_1['replacements']['<data_node>'] += "[ndbd]\nhostname=%s\ndatadir=/usr/local/mysql/data\n\n" % host

    for host in node_hosts['sql_nodes']:
        configuration_1['replacements']['<sql_node>'] += "[mysqld]\nhostname=%s\n\n" % host

    configurations.append(configuration_1)

    # configuration for my.cnf
    configuration_2 = {}
    configuration_2['file'] = 'my.cnf'
    configuration_2['replacements'] = {'<mgm_node_ip>': node_hosts['mgm_nodes'][0]}
    configurations.append(configuration_2)

    for configuration in configurations:
        infile = open('confs/base/'+configuration['file'])
        outfile = open('confs/'+configuration['file'], 'w')

        for line in infile:
            for src, target in configuration['replacements'].iteritems():
                line = line.replace(src, target)
            outfile.write(line)

        infile.close()
        outfile.close()

def kill_and_run(process, command, num_of_attempts=3):
    run('pkill %s' % process)
    for i in range(num_of_attempts):
        sleep(5)
        if not run('pgrep -l %s' % process):
            run(command)
            break


def install_mysql_cluster():
    run('mkdir -p src')
    if not exists('/usr/local/mysql-cluster'):
        with cd('src'):
            run('wget ' + env.mysql_cluster_download)
            run('tar zxf ' + env.mysql_cluster_filename)
            run('mv %s /usr/local/mysql-cluster' % env.mysql_cluster_filename.replace('.tar.gz', ''))


@roles("mgm_nodes")
def setup_mgm_nodes():
    install_mysql_cluster()

    run('mkdir -p /var/lib/mysql-cluster/')
    upload_template('conf/config.ini.jinja2', '/var/lib/mysql-cluster/config.ini', env.servers, use_jinja=True)
    run('/usr/local/mysql-cluster/bin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini --configdir=/var/lib/mysql-cluster --initial')


@roles("data_nodes")
def setup_data_nodes():
    install_mysql_cluster()

    upload_template('conf/my.cnf.jinja2', '/etc/my.cnf', env.servers, use_jinja=True)
    run('cat /etc/my.cnf')
    run('mkdir -p /var/lib/mysql-cluster/data')
    run('/usr/local/mysql-cluster/bin/ndbd --initial')


@roles("sql_nodes")
def setup_sql_nodes():
    require.deb.packages(
        ['libaio1', 'libaio-dev']
    )
    require.user('mysql')
    install_mysql_cluster()

    upload_template('conf/my.cnf.jinja2', '/etc/my.cnf', env.servers, use_jinja=True)

    run('mkdir -p /var/lib/mysql-cluster/data')
    if not exists('/var/lib/mysql-cluster/data/mysql'):
        run('/usr/local/mysql-cluster/scripts/mysql_install_db --user=mysql --basedir=/usr/local/mysql-cluster --datadir=/var/lib/mysql-cluster/data --defaults-file=/etc/my.cnf')

    if not exists('/etc/init.d/mysql.server'):
        run('cp /usr/local/mysql-cluster/support-files/mysql.server /etc/init.d')
        run("sed -i 's/^basedir=$/basedir=\/usr\/local\/mysql-cluster/g' /etc/init.d/mysql.server")
        run("sed -i 's/^datadir=$/datadir=\/var\/lib\/mysql-cluster\/data/g' /etc/init.d/mysql.server")

    require.service.started('mysql.server')


@roles("mgm_nodes")
def start_mgm_nodes():
    run('ndb_mgm -e shutdown')
    kill_and_run('ndb_mgmd', '/usr/local/bin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini --configdir=/var/lib/mysql-cluster --initial')

@roles("data_nodes")
def start_data_nodes():
    run('ndbd --initial')

@roles("sql_nodes")
def start_sql_nodes():
    kill_and_run('mysql', 'service mysql.server start')

def setup_mysql_cluster():
    execute(setup_mgm_nodes)
    execute(setup_data_nodes)
    execute(setup_sql_nodes)

def start_mysql_cluster():
    execute(start_mgm_nodes)
    execute(start_data_nodes)
    execute(start_sql_nodes)


@roles('mgm_nodes', 'sql_nodes', 'data_nodes')
def newrelic(newrelic_license_key):
    if not fabtools.files.exists('/etc/apt/sources.list.d/newrelic.list'):
        sudo('echo deb http://apt.newrelic.com/debian/ newrelic non-free >> /etc/apt/sources.list.d/newrelic.list')
        sudo('wget -O- https://download.newrelic.com/548C16BF.gpg | apt-key add -')
        sudo('apt-get update')

    require.deb.packages(['newrelic-sysmond'])
    sudo('nrsysmond-config --set license_key=' + newrelic_license_key)
    require.service.started('newrelic-sysmond')


@roles('mgm_nodes', 'sql_nodes', 'data_nodes')
def whatap(whatap_license_key):
    with settings(warn_only=True):
        if run('type whatap').return_code:
            sudo('wget http://repo.whatap.io/debian/release.gpg -O -|apt-key add -')
            sudo('wget http://repo.whatap.io/debian/whatap-repo_1.0_all.deb')
            sudo('dpkg -i whatap-repo_1.0_all.deb')
            sudo('apt-get update')
            require.deb.packages(['whatap-agent'])
            sudo('whatap ' + whatap_license_key)