import pySourceControl
from setuptools import setup, find_packages


'''readme'''
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()


'''setup'''
setup(
    name=pySourceControl.__title__,
    version=pySourceControl.__version__,
    description=pySourceControl.__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent'
    ],
    author=pySourceControl.__author__,
    url=pySourceControl.__url__,
    author_email=pySourceControl.__email__,
    license=pySourceControl.__license__,
    include_package_data=True,
    install_requires=[lab.strip('\n') for lab in list(open('requirements.txt', 'r').readlines())],
    zip_safe=True,
    packages=find_packages()
)