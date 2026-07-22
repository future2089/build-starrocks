import sys
path = sys.argv[1]
with open(path, 'r') as f:
    content = f.read()
old = '</configuration>'
new = '<property><name>dfs.datanode.sasl.embedded.http.server</name><value>true</value></property></configuration>'
content = content.replace(old, new)
with open(path, 'w') as f:
    f.write(content)
print('FIXED')
