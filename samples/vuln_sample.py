import os, subprocess, pickle, hashlib, requests, random

API_KEY = "sk_live_EXAMPLEonlyNOTaRealKey"            # hardcoded secret (synthetic demo value)
AWS = "AKIAIOSFODNN7EXAMPLE"                            # AWS key id

def run(cmd):
    os.system("ping " + cmd)                            # command injection
    subprocess.run("ls " + cmd, shell=True)             # command injection

def query(db, name):
    return db.execute("SELECT * FROM users WHERE name = " + name)   # SQL injection

def load(data):
    return pickle.loads(data)                           # unsafe deserialization

def token():
    return hashlib.md5(str(random.random()).encode()).hexdigest()  # weak hash + weak rng

def fetch(url):
    return requests.get(url)                            # possible SSRF

def read(request):
    return open("/data/" + request.path)                # path traversal

app_debug = True                                        # debug mode
r = requests.get("https://x", verify=False)             # TLS verify disabled
