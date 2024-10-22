#!/usr/bin/env python3

from subprocess import check_call
from argparse import ArgumentParser
from os import path
from buildinfo import version_to_buildinfo
from buildinfo import BuildInfo

BUILD_DIR = path.join(path.dirname(__file__))

def build_dockerfile(sha256, version, tags):
    build_command = ["docker", "build",
                     "--cache-from", "type=gha", "--cache-to", "type=gha",
                     "--build-arg", f"VERSION={version}",
                     "--build-arg", f"SHA256={sha256}"]
    for tag in tags:
        build_command += ["-t", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"]

    build_command.append(".")

    check_call(build_command, cwd=BUILD_DIR)

def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--push-tags", action="store_true")
    parser.add_argument("versions", nargs="*")
    args = parser.parse_args()

    versions_to_build = set()
    if not args.versions:
        versions_to_build.add("latest")
        versions_to_build.add("stable")
        versions_to_build.add("1.1.110")
    else:
        for version in args.versions:
            versions_to_build.add(version.lower())

    print(f"Trying to build versions: {versions_to_build}")

    builddata: list[BuildInfo] = []
    while versions_to_build:
        version = versions_to_build.pop()
        info = version_to_buildinfo(version)
        for tag in info.tags:
            versions_to_build.discard(tag)
        builddata.append(info)
        print(f"Will build container from {info.version} for tags {info.tags}")

    exit(1)

    for version, buildinfo in builddata.items():
        sha256 = buildinfo["sha256"]
        tags = buildinfo["tags"]
        build_dockerfile(sha256, version, tags)

    if not args.push_tags:
        return

    for version, buildinfo in builddata.items():
        for tag in tags:
            check_call(["docker", "push", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"])

if __name__ == "__main__":
    print(version_to_buildinfo("latest"))
    main()
