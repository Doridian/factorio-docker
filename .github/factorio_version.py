#!/usr/bin/env python3

from json import dumps, loads
from subprocess import check_call
from hashlib import sha256
from urllib.request import urlopen, Request

def http_make_req(url: str):
    return Request(url, headers={"User-Agent": "factorio_version.py (github.com/Doridian/factorio-docker)"})

def http_get_bytes(url: str) -> bytes:
    with urlopen(http_make_req(url)) as resp:
        return resp.read()

def http_get_str(url: str) -> str:
    with urlopen(http_make_req(url)) as resp:
        charset = resp.headers.get_content_charset("utf-8")
        return resp.read().decode(charset)

LOCAL_BUILDINFO = "./buildinfo.json"
LATEST_VERSION_URL = "https://factorio.com/api/latest-releases"

with open(LOCAL_BUILDINFO, "r") as fh:
    current_buildinfo = loads(fh.read())

latest_versions = loads(http_get_str(LATEST_VERSION_URL))

VERSION_LATEST = latest_versions["experimental"]["headless"]
VERSION_STABLE = latest_versions["stable"]["headless"]
VERSIONS_BUILDINFO = set([
    VERSION_LATEST,
    VERSION_STABLE,
    "1.1.110",
])

def version_to_url(version):
    return f"https://www.factorio.com/get-download/{version}/headless/linux64"

def version_to_buildinfo(version):
    info_sha256 = None
    if version in current_buildinfo:
        info_sha256 = current_buildinfo[version]["sha256"]
    else:
        print(f"Fetching {version} for SHA256")
        res = http_get_bytes(version_to_url(version))
        h = sha256()
        h.update(res)
        info_sha256 = h.hexdigest()
        print(f"SHA256: {info_sha256}")

    tags = [version]
    if version == VERSION_LATEST:
        tags.append("latest")
    if version == VERSION_STABLE:
        tags.append("stable")

    return {
        "sha256": info_sha256,
        "tags": tags,
    }

target_buildinfo = {}

for version in VERSIONS_BUILDINFO:
    target_buildinfo[version] = version_to_buildinfo(version)

if target_buildinfo == current_buildinfo:
    print("buildinfo.json already up to date")
    print("::set-output name=docker::false")
    exit(0)

current_buildinfo = dumps(target_buildinfo, indent=4)

with open(LOCAL_BUILDINFO, "w") as fh:
    fh.write(current_buildinfo)

check_call(["git", "add", "buildinfo.json"])
check_call(["git", "commit", "-m", "Update Factorio version(s)"])

print("buildinfo.json updated")
print("::set-output name=docker::true")
