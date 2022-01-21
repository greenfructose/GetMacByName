import subprocess
import re

subprocess = subprocess.Popen(f"getmac /s {compname} /fo csv", shell=True, stdout=subprocess.PIPE)
subprocess_return = subprocess.stdout.read()
regex = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
mac = re.search(regex, str(subprocess_return))
print(mac)