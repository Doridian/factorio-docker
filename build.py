#!/usr/bin/env python3

from subprocess import check_call, check_output
from argparse import ArgumentParser
from os import path
from buildinfo import version_to_buildinfo, BuildInfo
from ghcr import DOCKER_IMAGE_NAME, image_tag_exists, image_tag_equals

BUILD_DIR = path.join(path.dirname(__file__))

_git_rev = None
def get_git_rev() -> str:
    global _git_rev
    if _git_rev is not None:
        return _git_rev
    _git_rev = check_output(["git", "rev-parse", "HEAD"], text=True, cwd=BUILD_DIR).strip()
    return _git_rev

def build_dockerfile(info, /, push_tags: bool) -> None:
    build_command = [
        "docker", "buildx", "build",
        "--cache-from", "type=gha", "--cache-to", "type=gha",
        "--annotation", f"index,manifest,manifest-descriptor:factorio.version={info.version}",
        "--annotation", f"index,manifest,manifest-descriptor:factorio.sha256={info.sha256}",
        "--annotation", f"index,manifest,manifest-descriptor:factorio-docker.revision={get_git_rev()}",
        "--build-arg", f"VERSION={info.version}",
        "--build-arg", f"SHA256={info.sha256}",
        "--build-arg", f"GITREV={get_git_rev()}",
    ]
    for tag in info.tags:
        build_command += ["-t", f"{DOCKER_IMAGE_NAME}:{tag}"]

    if push_tags:
        build_command.append("--push")
    else:
        build_command.append("--load")

    build_command.append(".")

    check_call(build_command, cwd=BUILD_DIR)

def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--push-tags", action="store_true")
    parser.add_argument("--only-new" , action="store_true")
    parser.add_argument("versions", nargs="*")
    args = parser.parse_args()

    versions_to_build = set()
    if not args.versions:
        versions_to_build.add("latest")
        versions_to_build.add("stable")
        versions_to_build.add("1.1.110")
    else:
        for version in args.versions:
            versions_to_build.add(version.lower().strip())

    print(f"Instructed to build versions: {versions_to_build}")

    builddata: list[BuildInfo] = []
    while versions_to_build:
        version = versions_to_build.pop()
        info = version_to_buildinfo(version)

        for tag in info.tags:
            versions_to_build.discard(tag)

        if version not in info.tags:
            raise ValueError(f"Version {version} (game {info.version}) not in tags {info.tags}")

        builddata.append(info)
        print(f"Add build for container from {info.version} for tags {info.tags}")

    for info in builddata:
        if args.only_new and image_tag_exists(info.version):
            print(f"Already built version {info.version}, checking special tags")
            special_tag_needed = False
            for tag in info.tags:
                if tag == info.version:
                    continue
                if image_tag_equals(tag, info.version):
                    continue
                print(f"Special tag {tag} does not match {info.version}")
                special_tag_needed = True
                break

            if not special_tag_needed:
                print(f"Skipping all builds for {info.version} because it already exists and special tags match")
                continue

        build_dockerfile(info, push_tags=args.push_tags)

if __name__ == "__main__":
    main()
