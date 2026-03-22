from setuptools import setup, find_packages

import os

setup(
    name="mybackend",
    version="0.1",
    package_dir={"": "."},
    packages=find_packages(),
    description="My awesome backend",
    author="Loïc Dauphin",
    author_email="astralien3000@yahoo.fr",
    url="https://github.com/astralien3000/mybackend",
    install_requires=[
      "fastapi",
      "uvicorn",
      "authlib",
      "starlette",
      f"alterserv @ git+https://{os.environ['GITHUB_TOKEN']}@github.com/astralien3000/alterserv.git@master#egg=alterserv",
      "python-dotenv",
      "httpx",
      "itsdangerous",
    ],
)
