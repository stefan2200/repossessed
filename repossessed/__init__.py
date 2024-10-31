#!/usr/bin/python3

import os
import argparse
import sys
import tempfile
import requests
import tarfile
import subprocess
import logging
from . import classifier
from . import enumerator


def download_and_extract(build_blob_url, output_directory=None):

    # Set up file paths
    archive_path = os.path.join(output_directory, 'data.tgz')

    logging.info(f"Downloading {build_blob_url} to {archive_path}")

    # Download the file
    headers = {
        "User-Agent": "docker/20.10.8 go/go1.13.15 git-commit/fa9b5b2 kernel/4.19.128-microsoft-standard os/linux arch/amd64 UpstreamClient(Docker-Client/19.03.13 (linux))"
    }
    response = requests.get(build_blob_url, headers=headers, stream=True)
    response.raise_for_status()  # Check for request errors

    # Write the downloaded content to a file
    try:
        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.RequestException:
        return

    # Extract the tar file
    with tarfile.open(archive_path, 'r:gz') as tar:
        tar.extractall(path=output_directory)

    # Clean up the archive file after extraction
    os.remove(archive_path)
    return output_directory


def read_digests(read_manifest):
    digests = []
    if 'fsLayers' in read_manifest:
        for entry in read_manifest['fsLayers']:
            digests.append(entry['blobSum'])

    if 'layers' in read_manifest:
        for entry in read_manifest['layers']:
            digests.append(entry['digest'])
    return digests


def snipe_repo(host, repo, tag, index=0, first=0, run_on_folder=None, run_classifier=False):
    build_manifest = f"http://{host}/v2/{repo}/manifests/{tag}"
    get_manifest = requests.get(build_manifest, headers={
        "Accept": "application/vnd.oci.image.index.v1+json,application/vnd.oci.image.manifest.v1+json"})
    read_manifest = get_manifest.json()
    to_download = []
    get_digests = read_digests(read_manifest)
    if first:
        to_download = get_digests[0:first]
        if first == 99:
            # Skip last one, likely alpine
            to_download = to_download[:-1]
    elif index:
        if index == 99:
            index = len(get_digests)-1
        to_download = [get_digests[index]]
    temp_dir = tempfile.mkdtemp()
    logging.info(f"Downloading to temp directory: {temp_dir}")
    for digest in to_download:
        build_blob = f"http://{host}/v2/{repo}/blobs/{digest}"
        download_and_extract(build_blob, temp_dir)
    if run_classifier:
        classifier.run_classifier(temp_dir)
    if run_on_folder:
        subprocess.run([run_on_folder, temp_dir])
    print(f"Docker image data extracted to {temp_dir}")


def handle_enum(host, search=None):
    # Placeholder function for host enumeration
    logging.info(f"Enumerating host: {host}")
    repo_data = enumerator.get_repo_from_host(host)
    for repo in repo_data:
        if repo == "www.dreher.in":
            continue
        print(f"Repository: {repo}")
        tags = enumerator.get_repo_tags(host, repo=repo)
        for tag in tags:
            if search:
                if search not in repo or search not in tag:
                    continue
            print(f"Repository: {repo} Tag: {tag}")
            print(f"{sys.argv[0]} -H {host} -r {repo} -t {tag} --first 5")
        print("")


def clone_repo(host, output_directory):
    repo_data = enumerator.get_repo_from_host(host)
    for repo in repo_data:
        if repo == "www.dreher.in":
            continue
        create_repo_dir = os.path.join(output_directory, repo)
        if not os.path.exists(create_repo_dir):
            os.mkdir(create_repo_dir)
        tags = enumerator.get_repo_tags(host, repo=repo)
        for tag in tags:
            create_tag_dir = os.path.join(create_repo_dir, tag)
            print(f"Cloning: {repo}:{tag} To {create_tag_dir}")
            if not os.path.exists(create_tag_dir):
                os.mkdir(create_tag_dir)
            build_manifest = f"http://{host}/v2/{repo}/manifests/{tag}"
            get_manifest = requests.get(build_manifest, headers={
                "Accept": "application/vnd.oci.image.index.v1+json,application/vnd.oci.image.manifest.v1+json"})
            read_manifest = get_manifest.json()
            get_digests = read_digests(read_manifest)
            for digest in get_digests:
                build_blob = f"http://{host}/v2/{repo}/blobs/{digest}"
                download_and_extract(build_blob, create_tag_dir)


def main():
    # Create an OptionParser object
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Repossessed Docker Container Registry enumeration.")
    subparsers = parser.add_subparsers(dest="command", required=True,
                                       help="Subcommand to run (either 'enum' or 'dump')")

    # Enum subcommand parser
    enum_parser = subparsers.add_parser("enum", help="Enumerate host details.")
    enum_parser.add_argument("-H", "--host", required=True, help="Specify the host for enumeration.")
    enum_parser.add_argument("-s", "--search", required=False, default=None, help="Search for repos and tags")

    # Dump subcommand parser
    dump_parser = subparsers.add_parser("dump", help="Dump repository and search extracted files.")
    dump_parser.add_argument("-H", "--host", required=True, help="Specify the host (required)")
    dump_parser.add_argument("-r", "--repo", required=True, help="Specify the repository (required)")
    dump_parser.add_argument("-t", "--tag", required=True, help="Specify the tag (required)")
    dump_parser.add_argument("-i", "--index", default=0, type=int,
                             help="Specify the index (optional, default=0, use 99 for last layer)")
    dump_parser.add_argument("--first", default=None, type=int,
                             help="Specify the amount of indexes to download (99 for everything until the last)")
    dump_parser.add_argument("--run-on-folder", type=str, default=None,
                             help="Secondary command to execute on the folder")
    dump_parser.add_argument("-s", "--find-secrets", action="store_true",
                             help="Find secrets and passwords in common locations")

    clone_parser = subparsers.add_parser("clone", help="Clone an entire registry.")
    clone_parser.add_argument("-H", "--host", required=True, help="Specify the host (required)")
    clone_parser.add_argument("-O", "--output", required=True, help="Specify the output directory (required)")

    # Parse arguments
    args = parser.parse_args()

    # Handle subcommands
    if args.command == "enum":
        handle_enum(args.host, args.search)
    elif args.command == "dump":
        # Access and log dump arguments
        logging.info(f"Host: {args.host} Repo: {args.repo} Tag: {args.tag}")
        snipe_repo(args.host, args.repo, args.tag, args.index, args.first, args.run_on_folder, args.start_classifier)

    elif args.command == "clone":
        # Access and log dump arguments
        logging.info(f"Clone Host: {args.host} To {args.output}")
        clone_repo(args.host, args.output)
