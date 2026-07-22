import json, sys
d = json.load(sys.stdin)[0]
m = d.get("Mounts", [])
for x in m:
    print(f"  {x['Type']}: {x['Source']} -> {x['Destination']}")
print("Binds:", d["HostConfig"].get("Binds"))
print("NetworkMode:", d["HostConfig"].get("NetworkMode"))
print("IP:", d["NetworkSettings"].get("IPAddress"))
