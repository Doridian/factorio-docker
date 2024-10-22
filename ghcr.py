
from os import getenv
from base64 import b64encode
from httputil import http_get_str
from json import loads as json_loads
from urllib.error import HTTPError

_ghcr_repo = getenv("GITHUB_REPOSITORY", "doridian/factorio-docker").lower()
DOCKER_IMAGE_NAME = f"ghcr.io/{_ghcr_repo}/factorio"

_docker_auth = None
def get_docker_token() -> str:
    global _docker_auth
    if _docker_auth is not None:
        return _docker_auth

    actor = getenv("GITHUB_ACTOR")
    token = getenv("GITHUB_TOKEN")

    auth_creds = f"{actor}:{token}"
    auth_header = f"Basic {b64encode(auth_creds.encode()).decode()}"

    res = http_get_str(f"https://ghcr.io/token?scope=repository:{_ghcr_repo}:pull", headers={"Authorization": auth_header})
    data = json_loads(res)
    _docker_auth = f"Bearer {data['token']}"
    return _docker_auth

_image_tag_info = {}
def image_tag_info(tag: str) -> bool:
    tag = tag.lower()
    if tag in _image_tag_info:
        return _image_tag_info[tag]

    token = get_docker_token()

    try:
        res = json_loads(http_get_str(f"https://ghcr.io/v2/{DOCKER_IMAGE_NAME}/manifests/{tag}", headers={
            "Accept": "application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json",
            "Authorization": token,
        }))
        _image_tag_info[tag] = res
        return res
    except HTTPError as e:
        if e.code == 404:
            _image_tag_info[tag] = None
            return None
        raise

def image_tag_exists(tag: str) -> bool:
    return image_tag_info(tag) is not None

def image_tag_equals(tagA: str, tagB: str) -> bool:
    infoA = image_tag_info(tagA)
    infoB = image_tag_info(tagB)
    return infoA == infoB
