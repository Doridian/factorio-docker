#!/usr/bin/env python3

import os
import json
import subprocess
import shutil
import sys
import tempfile

def build_dockerfile(sha256, version, tags):
    build_dir = tempfile.mktemp()
    shutil.copytree("docker", build_dir)

    build_command = ["docker", "build",
                     "--cache-from", "type=gha", "--cache-to", "type=gha",
                     "--build-arg", f"VERSION={version}",
                     "--build-arg", f"SHA256={sha256}", "."]
    for tag in tags:
        build_command.extend(["-t", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"])

    subprocess.check_call(build_command, cwd=build_dir)

def pull_docker_tags(tags):
    for tag in tags:
        try:
            subprocess.check_call(["docker", "pull", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"])
        except:
            pass

def main(push_tags=False):
    with open(os.path.join(os.path.dirname(__file__), "buildinfo.json")) as file_handle:
        builddata = json.load(file_handle)

    for version, buildinfo in builddata.items():
        sha256 = buildinfo["sha256"]
        tags = buildinfo["tags"]
        pull_docker_tags(tags)
        build_dockerfile(sha256, version, tags)
        if not push_tags:
            continue
        for tag in tags:
            try:
                subprocess.run(["docker", "push", f"ghcr.io/doridian/factorio-docker/factorio:{tag}"],
                               check=True)
            except subprocess.CalledProcessError:
                print("Docker push failed")
                exit(1)


if __name__ == '__main__':
    push_tags = len(sys.argv) > 1 and sys.argv[1] == "--push-tags"
    main(push_tags)
