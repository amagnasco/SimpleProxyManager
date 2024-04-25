# do not call this file directly, instead use pip install
from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='SimpleProxyManager',
   version='0.1.0',
   description='Simple Python multithreaded proxy manager, focused on scrapes',
   license="CC-BY-SA-4.0",
   long_description=long_description,
   author='Alessandro G. Magnasco',
   author_email='amagnasco@gradcenter.cuny.edu',
   url="http://www.github.com/amagnasco/SimpleProxyManager",
   packages=['SimpleProxyManager'],
   install_requires=['requests', 'urllib3']
)