import subprocess

# Fix fe.conf - replace the JAVA_OPTS_FOR_JDK_11 line
cmd = """sed -i 's#^JAVA_OPTS_FOR_JDK_11 =.*#JAVA_OPTS_FOR_JDK_11 = -Dlog4j2.formatMsgNoLookups=true -Xmx8192m -XX:+UseG1GC -Dsun.security.krb5.debug=true -Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf -Djava.security.policy=/opt/starrocks/fe/conf/udf_security.policy#' /opt/starrocks/fe/conf/fe.conf"""
subprocess.run(['docker', 'exec', 'sr-deploy', 'sh', '-c', cmd], check=True)
print('Fixed fe.conf')

# Remove the old bad line
subprocess.run(['docker', 'exec', 'sr-deploy', 'sh', '-c', "sed -i '/^JAVA_OPTS_FOR_JDK_11= -Dsun/d' /opt/starrocks/fe/conf/fe.conf"], check=True)
print('Removed bad line')

# Verify
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'grep', 'JAVA_OPTS_FOR_JDK_11', '/opt/starrocks/fe/conf/fe.conf'], capture_output=True, text=True)
print(r.stdout.strip())
