#!/usr/bin/env python3
import subprocess
subprocess.run(['setenforce', '0'], check=True)
result = subprocess.run(['getenforce'], capture_output=True, text=True)
print(f'SELinux: {result.stdout.strip()}')
