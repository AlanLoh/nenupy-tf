from setuptools import setup, find_packages
import re
import nenupytf

meta_file = open('nenupytf/metadata.py').read()
metadata  = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", meta_file))

setup(
    name = 'nenupytf',
    packages = find_packages(),
    include_package_data = True,
    install_requires = ['numpy', 'astropy'],
    python_requires = '>=3.5',
    scripts = [],
    version = nenupytf.__version__,
    description = 'NenuFAR Python package',
    url = 'https://github.com/AlanLoh/nenupy-tf.git',
    author = metadata['author'],
    author_email = metadata['email'],
    license = 'MIT',
    zip_safe = False
    )


# Install on nancep
# /usr/local/bin/pip3.5 install nenupytf --install-option=--prefix=/cep/lofar/nenupytf --upgrade
