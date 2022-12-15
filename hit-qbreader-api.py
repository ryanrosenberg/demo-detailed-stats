import requests
import urllib.parse
import json

query = "2022 NASAT"

for pack in range(1, 21):
    url = "http://qbreader.org/api/packet?setName=" + urllib.parse.quote(query) + "&packetNumber=" + str(pack)

    resp = requests.get(url)

    resp_obj = json.dumps(resp.json())

    with open(f'packets/packet{pack}.json', 'w') as f:
        f.write(resp_obj)