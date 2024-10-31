import requests


def get_repo_tags(host, repo):
    try:
        url = f"http://{host}/v2/{repo}/tags/list"
        result = requests.get(url, timeout=(2, 5)).json()
        return result.get("tags", [])
    except:
        return get_repo_tags_maybe_tls(host, repo)


def get_repo_tags_maybe_tls(host, repo):
    try:
        url = f"https://{host}/v2/{repo}/tags/list"
        result = requests.get(url, verify=False, timeout=(2, 5)).json()
        return result.get("tags", [])
    except:
        return []


def maybe_tls(host):
    try:
        url = f"https://{host}/v2/_catalog"
        result = requests.get(url, verify=False, timeout=(2, 5)).json()
        return result.get("repositories", [])
    except:
        return []


def get_repo_from_host(host) -> list:
    try:
        url = f"http://{host}/v2/_catalog"
        result = requests.get(url, timeout=(2, 5))
        result = result.json()
        return result.get("repositories", [])
    except:
        return maybe_tls(host)
