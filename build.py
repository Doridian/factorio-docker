#!/usr/bin/env python3

from json import load as json_load
from subprocess import check_call, call
from argparse import ArgumentParser
from os import path

BUILD_DIR = path.join(path.dirname(__file__))

def build_dockerfile(sha256, version, tags):
    build_command = ["docker", "build",
                     "--cache-from", "type=gha", "--cache-to", "type=gha",
                     "--build-arg", f"VERSION={version}",
                     "--build-arg", f"SHA256={sha256}", "."]
    for tag in tags:
        build_command.extend(["-t", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"])

    check_call(build_command, cwd=BUILD_DIR)

def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--push-tags", action="store_true")
    args = parser.parse_args()

    with open(path.join(BUILD_DIR, "buildinfo.json")) as f:
        builddata = json_load(f)

    for version, buildinfo in builddata.items():
        sha256 = buildinfo["sha256"]
        tags = buildinfo["tags"]
        for tag in tags:
            call(["docker", "pull", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"])
        build_dockerfile(sha256, version, tags)

    if not args.push_tags:
        return

    for version, buildinfo in builddata.items():
        for tag in tags:
            check_call(["docker", "push", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"])

if __name__ == "__main__":
    main()
