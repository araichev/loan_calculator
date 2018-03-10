from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE.txt') as f:
    license = f.read()

setup(
    name='payulator',
    version='2.0.0',
    author='Alex Raichev',
    author_email='alex@raichev.net',
    url='https://github.com/araichev/payulator',
    license=license,
    description='A Python 3.5+ loan calculator',
    long_description=readme,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'pandas >= 0.22',
    ],
)
