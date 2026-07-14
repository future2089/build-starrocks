import subprocess, os, sys

# Use the host's Java 8 and Hive to create tables
host_env = os.environ.copy()
host_env['JAVA_HOME'] = '/usr'
host_env['HADOOP_HOME'] = '/data/bigdata/hadoop-3.3.6'
host_env['HIVE_HOME'] = '/data/bigdata/apache-hive-3.1.3-bin'
host_env['PATH'] = f'{host_env["HIVE_HOME"]}/bin:{host_env["HADOOP_HOME"]}/bin:/usr/bin:/bin'

def run_hive(conf_dir, query, label):
    env = host_env.copy()
    env['HIVE_CONF_DIR'] = conf_dir
    env['HADOOP_CONF_DIR'] = conf_dir
    r = subprocess.run(
        [f'{host_env["HIVE_HOME"]}/bin/hive', '-e', query],
        capture_output=True, text=True, env=env
    )
    stdout = r.stdout.strip()
    stderr = r.stderr.strip()
    print(f'{label}:')
    for line in (stdout + '\n' + stderr).split('\n'):
        if line.strip() and not line.startswith('SLF4J') and not line.startswith('WARNING'):
            print(f'  {line.strip()}')
    return r.returncode == 0

# Create tables for cluster_a
print('=== Cluster A ===')
run_hive('/data/starrocks-deploy/cluster_a/conf', 
    'CREATE DATABASE IF NOT EXISTS test_db; '
    'CREATE TABLE IF NOT EXISTS test_db.users (id INT, name STRING, age INT) '
    'ROW FORMAT DELIMITED FIELDS TERMINATED BY \",\" STORED AS TEXTFILE;',
    'create')

run_hive('/data/starrocks-deploy/cluster_a/conf',
    'SHOW DATABASES;',
    'databases')

# Create tables for cluster_b
print('\n=== Cluster B ===')
run_hive('/data/starrocks-deploy/cluster_b/conf',
    'CREATE DATABASE IF NOT EXISTS test_db; '
    'CREATE TABLE IF NOT EXISTS test_db.products (pid INT, pname STRING, price DOUBLE) '
    'ROW FORMAT DELIMITED FIELDS TERMINATED BY \",\" STORED AS TEXTFILE;',
    'create')

run_hive('/data/starrocks-deploy/cluster_b/conf',
    'SHOW DATABASES;',
    'databases')

# Insert test data
run_hive('/data/starrocks-deploy/cluster_a/conf',
    'INSERT INTO test_db.users VALUES (1, \"Alice\", 30), (2, \"Bob\", 25);',
    'insert_a')

run_hive('/data/starrocks-deploy/cluster_b/conf',
    'INSERT INTO test_db.products VALUES (101, \"Widget\", 9.99), (102, \"Gadget\", 19.99);',
    'insert_b')

# Verify
run_hive('/data/starrocks-deploy/cluster_a/conf', 'SELECT * FROM test_db.users;', 'select_a')
run_hive('/data/starrocks-deploy/cluster_b/conf', 'SELECT * FROM test_db.products;', 'select_b')

print('\nDONE')
