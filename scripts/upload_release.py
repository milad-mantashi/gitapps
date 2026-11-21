"""Attach built packages and checksums to the release that triggered CI."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
url = event['release']['upload_url'].split('{')[0]
for asset in sorted(Path('dist').iterdir()):
    if asset.suffix not in {'.deb', '.rpm'}:
        continue
    checksum = asset.with_name(asset.name + '.sha256')
    checksum.write_text(hashlib.sha256(asset.read_bytes()).hexdigest() + '  ' + asset.name + '\n')
    for file in [asset, checksum]:
        request = Request(url + '?name=' + quote(file.name), data=file.read_bytes(), method='POST',
                          headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                                   'Content-Type': 'application/octet-stream',
                                   'Accept': 'application/vnd.github+json'})
        with urlopen(request, timeout=120) as response:
            result = json.load(response)
        print('Uploaded:', result['name'])
