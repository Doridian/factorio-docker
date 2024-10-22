#!/usr/bin/env python3

from json import loads as json_loads
from httputil import http_get_str, http_make_req
from re import split as re_split
from os import path
from urllib.parse import urlparse
from dataclasses import dataclass

LATEST_VERSION_URL = "https://www.factorio.com/api/latest-releases"
SHA256SUM_URL = "https://www.factorio.com/download/sha256sums/"

VERSION_LATEST = None
VERSION_STABLE = None

_special_versions_fetched = False
def fetch_special_versions():
    global VERSION_LATEST, VERSION_STABLE, _special_versions_fetched
    if _special_versions_fetched:
        return

    latest_versions = json_loads(http_get_str(LATEST_VERSION_URL))

    VERSION_LATEST = latest_versions["experimental"]["headless"]
    VERSION_STABLE = latest_versions["stable"]["headless"]
    _special_versions_fetched = True
    #VERSIONS_BUILDINFO = set([
    #    VERSION_LATEST,
    #    VERSION_STABLE,
    #    "1.1.110",
    #])

SHA256SUMS = None
def fetch_sha256sums():
    global SHA256SUMS
    if SHA256SUMS is not None:
        return

    lines = http_get_str(SHA256SUM_URL).splitlines()
    newsums = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        sha256sum, filename = re_split("\\s+", line)
        newsums[filename] = sha256sum
    SHA256SUMS = newsums

_version_filenames = {}

@dataclass(eq=True, frozen=True, kw_only=True)
class BuildInfo:
    tags: list[str]
    sha256: str
    version: str
    url: str


def _try_find_version_filename(version: str) -> str:
    static_tries = [
        f"factorio_headless_x64_{version}.tar.xz",
        f"factorio-headless_linux_{version}.tar.xz",
    ]

    for filename in static_tries:
        if filename in SHA256SUMS:
            return filename

    for candidate in SHA256SUMS.keys():
        if "headless" not in candidate:
            continue
        if not candidate.endswith(f"_{version}.tar.xz"):
            continue
        return candidate

    return ""

def version_to_buildinfo(version: str):
    fetch_special_versions()
    fetch_sha256sums()

    if version == "latest":
        version = VERSION_LATEST
    elif version == "stable":
        version = VERSION_STABLE

    url = f"https://www.factorio.com/get-download/{version}/headless/linux64"

    if version in _version_filenames:
        filename = _version_filenames[version]
    else:
        filename = _try_find_version_filename(version)
        if (not filename) or (filename not in SHA256SUMS):
            with http_make_req(url, follow_redirects=False) as resp:
                file_url = resp.headers["location"]

            parsed_url = urlparse(file_url)
            filename = path.basename(parsed_url.path)
        _version_filenames[version] = filename

    tags = [version]
    if version == VERSION_LATEST:
        tags.append("latest")
    if version == VERSION_STABLE:
        tags.append("stable")

    version_split = version.split(".")
    for i in range(1, len(version_split)):
        f_version = ".".join(version_split[:i])
        tags.append(f"{f_version}.x")


    return BuildInfo(
        sha256=SHA256SUMS[filename],
        version=version,
        url=url,
        tags=tags,
    )
