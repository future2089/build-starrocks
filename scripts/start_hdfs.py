#!/usr/bin/env python3
import subprocess
import os
import time

env = os.environ.copy()
env["JAVA_HOME"] = "/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.462.b08-4.oe2403sp2.x86_64"
env["HADOOP_HOME"] = "/data/package/hadoop-3.3.6"
env["HADOOP_CONF_DIR"] = env["HADOOP_HOME"] + "/etc/hadoop"
env["PATH"] = env["HADOOP_HOME"] + "/bin:" + env["HADOOP_HOME"] + "/sbin:" + env["PATH"]
env["HADOOP_ROOT_LOGGER"] = "INFO,console"
HADOOP_HOME = env["HADOOP_HOME"]

def run(cmd):
    print("Running:", cmd)
    result = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:])
    print("STDOUT:", result.stdout[-300:])
    return result.returncode

# Format HDFS
print("=== Formatting HDFS ===")
run(HADOOP_HOME + "/bin/hdfs namenode -format -force")

# Start NameNode
print("\n=== Starting NameNode ===")
run(HADOOP_HOME + "/sbin/hadoop-daemon.sh start namenode")
time.sleep(3)

# Start DataNode
print("\n=== Starting DataNode ===")
run(HADOOP_HOME + "/sbin/hadoop-daemon.sh start datanode")
time.sleep(3)

# Verify
print("\n=== Verification ===")
run(HADOOP_HOME + "/bin/hdfs dfsadmin -report")

print("\n=== Start MySQL ===")
subprocess.run("mysqld_safe --user=root &", shell=True, capture_output=True, timeout=5)
time.sleep(3)

# Initialize Hive schema
print("\n=== Initialize Hive Schema ===")
hive_env = env.copy()
hive_env["HIVE_HOME"] = "/data/package/apache-hive-3.1.3-bin"
run(hive_env["HIVE_HOME"] + "/bin/schematool -dbType mysql -initSchema")

# Start HMS
print("\n=== Starting Hive Metastore ===")
hive_cmd = (hive_env["HIVE_HOME"] + "/bin/hive --service metastore -p 9083 &")
subprocess.run(hive_cmd, shell=True, env=hive_env, capture_output=True, timeout=10)
time.sleep(5)

print("\n=== HDFS+HMS Setup Complete ===")
print("HDFS: hdfs://arm-ha (192.168.0.181:8020)")
print("HMS: thrift://192.168.0.181:9083 (Kerberos)")
