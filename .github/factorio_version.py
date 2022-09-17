#!/usr/bin/env python3

from json import dumps, loads
from requests import get

LOCAL_BUILDINFO = "./buildinfo.json"
BUILDINFO_URL = ""

with open(LOCAL_BUILDINFO, "r") as fh:
    buildinfo_local = loads(fh.read())

print(buildinfo_local)
