#!/usr/bin/env python3

# Update the DNS TXT record for a cloudflare website to point to the latest ipfs object.
# We prefer that the TXT record points to the specific IPFS object rather than
# an IPNS id because the cost of doing a IPNS lookup for EVERY request is too high.

# How does the TXT record work?
# see https://github.com/ipfs/notes/issues/39
# point yourdomain.com to gateway.ipfs.io (either via A record or a flattened CNAME record).
# Add a TXT entry to _dnslink.yourdomain.com with contens: "dnslink=/ipfs/Qmfoo"
#
# OLD METHOD:
##### see https://github.com/diasdavid/ipscend#use-ipfs-to-host-your-webpage-using-a-standard-domain-includes-cool-dns-trick
##### If we alias ipfs.yourdomain.com to ipfs.io and then create a DNS TXT entry with
##### name: "ipfs",
##### content: "dnslink=/ipfs/QmRpCcmoMWVEa8mYn1bczeUDxS2QUcsysodPUBuMkxfzPN"
##### Then ipfs.yourdomain.com will serve the IPFS object indicated above
##### ipfs.yourdomain.com/XYZ will serve the IPFS object: QmRpCcmoMWVEa8mYn1bczeUDxS2QUcsysodPUBuMkxfzPN/XYZ

import json, requests, sys

# Cloudflare Name for the DNS TXT entries that we wish to link to IPFS, plus the root address relative to the ipfs folder we publish.
dnslink_subdomains = {
    "mooooo.ooo": {
        "mooooo.ooo": ""
        # "test.mooooo.ooo": "" # Example for subdomains.
    },
    "pinkie.party": {
        "pinkie.party": "/pinkie-party"
    },
    "shadilay.party": {
        "shadilay.party": "/shadilay-party"
    }
}

user_email = "wallacoloo@gmail.com"

def api_call(api_key, api_path, params=None, method="GET", data=None):
    """Make an API call to the given url with params=dict(), data=object() or None.
    `data` will be cast to JSON before being sent.
    The response is a python dict, parsed from the server's JSON response."""
    headers = {
            'X-Auth-Email': user_email,
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
    }
    r = requests.request(method, "https://api.cloudflare.com/client/v4" + api_path, params=params, headers=headers, data=json.dumps(data) if data else None)
    print(r.text)
    return json.loads(r.text)

def get_zone_id(api_key, site_name):
    """Return the CloudFlare id of the website with name 'site_name'"""
    r = api_call(api_key, "/zones", params={'name': site_name})
    return r["result"][0]["id"]

def get_dns_txt_info(api_key, zone_id, dns_name):
    """Return the CloudFlare id of the DNS TXT entry with name=ipfs for the given zone_id"""
    r = api_call(api_key, "/zones/%s/dns_records" %zone_id, params={'type': 'TXT', 'name': dns_name})
    return r["result"][0]

def update_txt_record(api_key, zone_id, record_data):
    """Update the TXT dns record to direct to the given ipfs object"""
    r = api_call(api_key, "/zones/%s/dns_records/%s" %(zone_id, record_data["id"]), method="PUT", data=record_data)

def purge_cache(api_key, zone_id):
    """Purge all files in the given zone from Cloudflare's cache"""
    r = api_call(api_key, "/zones/%s/purge_cache" %zone_id, method="DELETE", data={"purge_everything": True})

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <API Key> <IPFS id of website root>" %(sys.argv[0] if sys.argv else "update_cloudflare.py"))
        sys.exit(1)

    api_key = sys.argv[1]
    ipfs_id = sys.argv[2]
    
    for zone_name, dnslinks in dnslink_subdomains.items():
        zone_id = get_zone_id(api_key, zone_name)
        for sub, leaf in dnslinks.items():
            print("updating", sub, "for", zone_name)
            dns_entry = get_dns_txt_info(api_key, zone_id, sub)
            dns_entry["content"] = "dnslink=/ipfs/%s" %ipfs_id + leaf
            update_txt_record(api_key, zone_id, dns_entry)
        purge_cache(api_key, zone_id)

