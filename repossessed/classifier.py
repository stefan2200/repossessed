import os
import mimetypes
import logging

# List of extensions for known readable file types
READABLE_EXTENSIONS = {'.json', '.yaml', '.yml', '.env', '.txt', '.csv', '.md', '.conf'}


def is_readable_file(file_path):
    # Check if the file has a readable MIME type or known extension
    mime_type, _ = mimetypes.guess_type(file_path)
    extension = os.path.splitext(file_path)[1].lower()

    # Consider the file readable if MIME type starts with "text" or if it has a readable extension
    return (
            (mime_type and mime_type.startswith('text')) or
            (mime_type in {'application/json', 'application/x-yaml'}) or  # Add JSON, YAML MIME types
            (extension in READABLE_EXTENSIONS)
    )


def find_common_files(root_directory):
    common_files = [
        "app/.env",
        "app/.env.prd",
        "app/.env.prod",
        "app/.gitlab-ci.yml",
        "app/appsetting.json",
        "app/appsettings.Production.json",
        "app/config",
        "app/.env.production"
    ]
    for entry in common_files:
        check_file = os.path.join(root_directory, entry)
        if os.path.exists(check_file):
            logging.info("File or directory %s exists and might contain valuable information", entry)


def check_spring_boot(root_directory):
    file_list = os.listdir(root_directory)
    for file in file_list:
        if file.endswith(".jar") or file.endswith(".war"):
            merged = os.path.join(root_directory, file)
            logging.info("Likely spring boot application, found in %s use a tool like jd-gui to decompile", merged)
            return True
    return False


def search_extracted_files(search_term, directory, max_file_size=5 * 1024 * 1024):
    matches = []

    # Traverse directories recursively with os.walk
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if "app" not in file_path and "html" not in file_path:
                continue
            if "node_modules" in file_path:
                continue
            if "lib" in file_path:
                continue

            # Attempt to open and search each file
            try:
                # Check file size and skip if it exceeds max_file_size
                if os.path.getsize(file_path) > max_file_size:
                    logging.debug(f"Skipping large file: {file_path}")
                    continue

                # Check if the file is likely readable
                if not is_readable_file(file_path):
                    logging.debug(f"Skipping non-readable file: {file_path}")
                    continue
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line_number, line in enumerate(file, start=1):
                        if search_term in line:
                            # If a match is found, store the result
                            matches.append((file_path, line_number, line.strip()))
            except (UnicodeDecodeError, IOError, OSError, FileNotFoundError):
                # Skip files that can't be decoded or opened as text
                logging.debug(f"Could not read {file_path} due to encoding or I/O error")
            except PermissionError:
                # Handle files that the user cannot access due to permission issues
                logging.debug(f"Permission denied: {file_path}")

    # Print or return all matches found
    for match in matches:
        logging.info(f"Match found in {match[0]} on line {match[1]}: {match[2]}")

    return matches  # Returns list of matches for further processing if needed


def find_amazon_key(target_directory):
    search_extracted_files("AWS", target_directory)
    aws_regions = [
        "us-east-1",  # US East (N. Virginia)
        "us-east-2",  # US East (Ohio)
        "us-west-1",  # US West (N. California)
        "us-west-2",  # US West (Oregon)
        "af-south-1",  # Africa (Cape Town)
        "ap-east-1",  # Asia Pacific (Hong Kong)
        "ap-south-1",  # Asia Pacific (Mumbai)
        "ap-south-2",  # Asia Pacific (Hyderabad)
        "ap-southeast-1",  # Asia Pacific (Singapore)
        "ap-southeast-2",  # Asia Pacific (Sydney)
        "ap-southeast-3",  # Asia Pacific (Jakarta)
        "ap-northeast-1",  # Asia Pacific (Tokyo)
        "ap-northeast-2",  # Asia Pacific (Seoul)
        "ap-northeast-3",  # Asia Pacific (Osaka)
        "ca-central-1",  # Canada (Central)
        "eu-central-1",  # Europe (Frankfurt)
        "eu-central-2",  # Europe (Zurich)
        "eu-west-1",  # Europe (Ireland)
        "eu-west-2",  # Europe (London)
        "eu-west-3",  # Europe (Paris)
        "eu-north-1",  # Europe (Stockholm)
        "eu-south-1",  # Europe (Milan)
        "eu-south-2",  # Europe (Spain)
        "me-south-1",  # Middle East (Bahrain)
        "me-central-1",  # Middle East (UAE)
        "sa-east-1"  # South America (São Paulo)
    ]
    for region in aws_regions:
        search_extracted_files(region, target_directory)


def find_passwords_key(target_directory):
    secrets = [
        "jwt",
        "JWT",
        "s3",
        "S3",
        "password",
        "PASSWORD",
        "secret",
        "SECRET",
        "Database="
    ]
    for secret in secrets:
        search_extracted_files(secret, target_directory)


def run_classifier(target_directory):
    if not check_spring_boot(target_directory):
        find_amazon_key(target_directory)
        find_passwords_key(target_directory)
        find_common_files(target_directory)

