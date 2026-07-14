# Generate SQL files for creating catalogs
import os

sql_dir = '/tmp/starrocks_sql'
os.makedirs(sql_dir, exist_ok=True)

# Create catalog A
with open(f'{sql_dir}/catalog_a.sql', 'w') as f:
    f.write("CREATE EXTERNAL CATALOG hive_a PROPERTIES (\n")
    f.write("    \"type\"=\"hive\",\n")
    f.write("    \"hive.metastore.uris\"=\"thrift://192.168.0.211:9084\",\n")
    f.write("    \"aws.s3.use_instance_profile\"=\"false\",\n")
    f.write("    \"aws.s3.access_key\"=\"\",\n")
    f.write("    \"aws.s3.secret_key\"=\"\",\n")
    f.write("    \"aws.s3.region\"=\"us-east-1\"\n")
    f.write(");\n")
    f.write("SHOW CATALOGS;\n")

# Create catalog B
with open(f'{sql_dir}/catalog_b.sql', 'w') as f:
    f.write("CREATE EXTERNAL CATALOG hive_b PROPERTIES (\n")
    f.write("    \"type\"=\"hive\",\n")
    f.write("    \"hive.metastore.uris\"=\"thrift://192.168.0.211:9085\",\n")
    f.write("    \"aws.s3.use_instance_profile\"=\"false\",\n")
    f.write("    \"aws.s3.access_key\"=\"\",\n")
    f.write("    \"aws.s3.secret_key\"=\"\",\n")
    f.write("    \"aws.s3.region\"=\"us-east-1\"\n")
    f.write(");\n")
    f.write("SHOW CATALOGS;\n")

print(f'SQL files created in {sql_dir}')
