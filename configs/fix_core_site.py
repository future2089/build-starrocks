import subprocess

core_site = '''<configuration>
  <property>
      <name>fs.s3.impl</name>
      <value>org.apache.hadoop.fs.s3a.S3AFileSystem</value>
   </property>
   <property>
      <name>hadoop.security.auth_to_local</name>
      <value>
        RULE:[1:$1](hive/.*@SR.TEST)s/.*/hive/
        RULE:[1:$1](hive/.*@ARM.SR.TEST)s/.*/hive/
        RULE:[2:$1@$0](.*)s/.*/hive/
        DEFAULT
      </value>
   </property>
</configuration>'''

# Write to 211 first
with open('/tmp/core-site.xml', 'w') as f:
    f.write(core_site)

# Copy to sr-deploy container
r = subprocess.run(['docker', 'cp', '/tmp/core-site.xml', 'sr-deploy:/opt/starrocks/fe/conf/core-site.xml'], capture_output=True, text=True, timeout=15)
print('Copy:', r.stderr.strip()[:200] if r.stderr else 'OK')

# Verify
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'cat', '/opt/starrocks/fe/conf/core-site.xml'], capture_output=True, text=True, timeout=10)
print('Verify:', r.stdout[:500])
