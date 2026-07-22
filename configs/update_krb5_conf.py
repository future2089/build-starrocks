import subprocess

krb5_conf = r"""[logging]
 default = FILE:/var/log/krb5libs.log
 kdc = FILE:/var/log/krb5kdc.log
 admin_server = FILE:/var/log/kadmind.log

[libdefaults]
 dns_lookup_realm = false
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true
 rdns = false
 default_realm = SR.TEST
 dns_lookup_kdc = false

[realms]
 SR.TEST = {
  kdc = 192.168.0.211:88
  admin_server = 192.168.0.211:749
  default_domain = sr.test
 }
 ARM.SR.TEST = {
  kdc = 192.168.0.181:88
  admin_server = 192.168.0.181:749
  default_domain = arm.sr.test
 }

[domain_realm]
 .sr.test = SR.TEST
 sr.test = SR.TEST
 .arm.sr.test = ARM.SR.TEST
 arm.sr.test = ARM.SR.TEST
 arm-hive = ARM.SR.TEST
 192.168.0.181 = ARM.SR.TEST
"""

subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'tee', '/opt/starrocks/fe/meta/krb5.conf'], input=krb5_conf, text=True, timeout=10)
print('krb5.conf updated')

r = subprocess.run(['docker', 'exec', 'sr-deploy', 'grep', 'arm-hive', '/opt/starrocks/fe/meta/krb5.conf'], capture_output=True, text=True, timeout=10)
print('Verified:', r.stdout.strip()[:200])
