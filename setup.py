# do not call this file directly, instead use pip install
from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='proxyManager',
   version='0.0.1',
   description='Simple Python multithreaded proxy manager, focused on scrapes',
   license="CC-BY-SA-4.0",
   long_description=long_description,
   author='Alessandro G. Magnasco',
   author_email='amagnasco@gradcenter.cuny.edu',
   url="http://www.github.com/amagnasco/proxyManager",
   packages=['proxyManager'],
   install_requires=['asyncio', 'urllib3'],
   dev=['dev/example']
)