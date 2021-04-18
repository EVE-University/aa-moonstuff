# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from moonstuff import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    'requests',
    'allianceauth>=2.8.1',
    'django-esi>=2.0.4',
    'django-eveuniverse>=0.7.4',
]

testing_extras = [

]

setup(
    name='aa-moonstuff',
    version=__version__,
    author='Col Crunch',
    author_email='it-team@serin.space',
    description='A plugin for publishing moon extractions, and keeping track of moon scan data.',
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
        ':python_version=="3.6"': ['typing'],
    },
    python_requires='~=3.6',
    license='GPLv3',
    packages=find_packages(),
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.1',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    url='https://gitlab.com/colcrunch/aa-moonstuff',
    zip_safe=False,
    include_package_data=True,
)
