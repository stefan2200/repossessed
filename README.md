# Repossessed
**Docker container registry enumeration and downloader.**

```text
> Can you write me a three line partially technical management summary why you should not store production credentials in the source code of an application? <
Storing production credentials in source code exposes sensitive information to unauthorized access, especially if the code is shared or publicly accessible. 
This practice significantly increases security risks, as credentials are susceptible to accidental exposure, breaches, or leaks.
Proper credential management, such as using environment variables or secret management tools, ensures security and compliance with best practices.
```

Read that again and replace `source code` with `docker container`.

How do I find these? well this Shodan query might help:
```text
port:5000 docker
```

At the time of writing there appear to be 5.500 unprotected repositories with roughly 400.000 exposed docker images.

Installation:

```text
$ git clone https://github.com/stefan2200/repossessed
$ cd repossessed
$ python3 -m pip install -r requirements.txt
$ python3 repossessed.py -h
usage: repossessed.py [-h] {enum,dump,clone} ...

Or
$ python3 setup.py install
$ repossessed -h
usage: repossessed [-h] {enum,dump,clone} ...
```

Usage for enumeration:

```text
usage: repossessed.py enum [-h] -H HOST [-s SEARCH]

options:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Specify the host for enumeration.
  -s SEARCH, --search SEARCH
                        Search for repos and tags
```

Example enumeration:

```text
$ python repossessed.py enum -H xx.xx.xx.xx:5000
INFO:root:Enumerating host: xx.xx.xx.xx:5000
Repository: admin
Repository: admin Tag: latest
repossessed -H xx.xx.xx.xx:5000 -r admin -t latest --first 5

Repository: frontend
Repository: frontend Tag: latest
repossessed -H xx.xx.xx.xx:5000 -r frontend -t latest --first 5

Repository: backend
Repository: backend Tag: latest
repossessed -H xx.xx.xx.xx:5000 -r backend -t latest --first 5
```

Usage to download and automatically search a repository:

```text
usage: repossessed.py dump [-h] -H HOST -r REPO -t TAG [-i INDEX] [--first FIRST] [--run-on-folder RUN_ON_FOLDER] [-s]

options:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Specify the host (required)
  -r REPO, --repo REPO  Specify the repository (required)
  -t TAG, --tag TAG     Specify the tag (required)
  -i INDEX, --index INDEX
                        Specify the index (optional, default=0, use 99 for last layer)
  --first FIRST         Specify the amount of indexes to download (99 for everything until the last)
  --run-on-folder RUN_ON_FOLDER
                        Secondary command to execute on the folder
  -s, --find-secrets
                        Find secrets and passwords in common locations

```

Example usage:

```text
Clone the entire repo
$ python repossessed.py dump -H xx.xx.xx.xx:5000 -r payment-service -t v1.3.0

Clone the entire repo and automatically scan for secrets and passwords:
$ python repossessed.py dump -H xx.xx.xx.xx:5000 -r payment-service -t v1.3.0 -s

Clone the repo partially and launch the Sublime Text editor in the directory
$ python repossessed.py dump -H xx.xx.xx.xx:5000 -r payment-service -t v1.3.0 --run-on-folder subl

Clone the complete registry to a folder
$ python repossessed.py clone -H xx.xx.xx.xx:5000 -O /tmp/registry-clone/
```


