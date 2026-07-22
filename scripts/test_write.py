#!/usr/bin/env python3
f = open("/etc/hadoop/conf/test.txt", "w")
f.write("hello\n")
f.close()
print("PYTHON_WRITE_OK")
