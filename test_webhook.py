import urllib.request
import hmac
import hashlib
import json

secret = b"mysecret" # TODO: get from cicd_config
payload = {
    "ref": "refs/heads/main",
    "repository": {
        "name": "Rivera-cv",
        "clone_url": "https://github.com/afrivera/Rivera-cv.git"
    },
    "head_commit": {
        "message": "test commit",
        "author": {"username": "afrivera"}
    }
}
body = json.dumps(payload).encode('utf-8')
signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

req = urllib.request.Request("http://127.0.0.1:8083/api/webhooks/github", data=body, headers={
    "X-GitHub-Event": "push",
    "X-Hub-Signature-256": signature
}, method="POST")

try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Response:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.code)
    print("Response:", e.read().decode())
