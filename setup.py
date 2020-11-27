# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="push_to_gdoc",
    version="0.1.0",
    description="Get data from python into Google Docs",
    author="David Raznick",
    author_email="david.raznick@opendataservices.coop",
    url="https://github.com/OpenDataServices/push_to_gdoc/",
    license=license,
    packages=find_packages(exclude=("tests", "docs")),
    install_requires=[
        'matplotlib',
        'pandas',
        'appdirs',
        'google-api-python-client',
        'google_auth_oauthlib',
        'google'
    ],
    extras_require={
        'test': [
            'pytest',
            'black'
        ],
    }
)
