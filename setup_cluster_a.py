import subprocess, os, shutil

# Environment
HADOOP_HOME = '/usr/local/hadoop'
HIVE_HOME = '/usr/local/hive'
JAVA_HOME = '/usr/lib/jvm/java-11-openjdk-amd64'
CONF_SRC = '/data/deploy/conf'

HADOOP_CONF_DIR = '/data/deploy/hadoop-conf'
HIVE_CONF_DIR = '/data/deploy/hive-conf'

# Create conf dirs
os.makedirs(HADOOP_CONF_DIR, exist_ok=True)
os.makedirs(HIVE_CONF_DIR, exist_ok=True)
os.makedirs('/data/deploy/logs', exist_ok=True)

# Copy Hadoop config files
for f in ['core-site.xml', 'hdfs-site.xml']:
    shutil.copy2(f'{CONF_SRC}/{f}', f'{HADOOP_CONF_DIR}/{f}')

# Copy Hive config
shutil.copy2(f'{CONF_SRC}/hive-site.xml', f'{HIVE_CONF_DIR}/hive-site.xml')

# Copy krb5.conf
shutil.copy2(f'{CONF_SRC}/krb5.conf', '/etc/krb5.conf')

# Write env setup script
with open('/etc/profile.d/hive-env.sh', 'w') as f:
    f.write(f'''export JAVA_HOME={JAVA_HOME}
export HADOOP_HOME={HADOOP_HOME}
export HADOOP_CONF_DIR={HADOOP_CONF_DIR}
export HIVE_HOME={HIVE_HOME}
export HIVE_CONF_DIR={HIVE_CONF_DIR}
export PATH=$PATH:$HADOOP_HOME/bin:$HIVE_HOME/bin
''')

print('Env setup done')
