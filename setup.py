from setuptools import setup, find_packages

setup(
    name="Repossessed",
    version="1.0.0",
    description="A tool for docker container registry enumeration",
    author="stefan2200",
    url="https://github.com/stefan2200/repossessed",
    packages=find_packages(),
    py_modules=["repossessed"],
    entry_points={
        "console_scripts": [
            "repossessed=repossessed:main",
        ],
    },
    install_requires=["requests"],
)
