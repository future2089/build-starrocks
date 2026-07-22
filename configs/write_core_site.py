import subprocess

core_site = """<configuration>
  <property>
      <name>fs.s3.impl</name>
      <value>org.apache.hadoop.fs.s3a.S3AFileSystem</value>
   </property>
   <property>
      <name>hadoop.security.auth_to_local</name>
      <value>
        RULE:[2:$1@$0](hive/arm-hive@ARM.SR.TEST)s/.*/hive/
        RULE:[2:$1@$0](hive/cluster_a@SR.TEST)s/.*/hive/
        RULE:[2:$1@$0](hive/cluster_b@SR.TEST)s/.*/hive/
        DEFAULT
      </value>
   </property>
</configuration>
"""

with open('/tmp/core-site.xml', 'w') as f:
    f.write(core_site)

r = subprocess.run(['docker', 'cp', '/tmp/core-site.xml', 'sr-deploy:/opt/starrocks/fe/conf/core-site.xml'], capture_output=True, text=True)
print('cp:', r.stderr[:200] if r.stderr else 'OK')

r = subprocess.run(['docker', 'exec', 'sr-deploy', 'cat', '/opt/starrocks/fe/conf/core-site.xml'], capture_output=True, text=True)
print(r.stdout)
