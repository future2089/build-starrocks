#!/usr/bin/env python3
import os
path = "/etc/hadoop/conf/test.txt"
print("exists:", os.path.exists(path))
try:
    f = open(path, "r")
    print("content:", f.read())
    f.close()
except Exception as e:
    print("read error:", e)
try:
    f = open(path, "w")
    f.write("from_second_write\n")
    f.close()
    print("second write OK")
except Exception as e:
    print("write error:", e)
