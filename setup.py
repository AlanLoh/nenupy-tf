from setuptools import setup, find_packages
import re
import nenupytf

meta_file = open('nenupytf/metadata.py').read()
metadata  = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", meta_file))

setup(
    name = 'nenupytf',
    packages = find_packages(),
    include_package_data = True,
    install_requires = ['numpy', 'astropy', 'psutil'],
    python_requires = '>=3.5',
    scripts = [
        'bin/nenupytf-plot',
        'bin/nenupytf-info'
        ],
    version = nenupytf.__version__,
    description = 'NenuFAR Python package',
    url = 'https://github.com/AlanLoh/nenupy-tf.git',
    author = metadata['author'],
    author_email = metadata['email'],
    license = 'MIT',
    zip_safe = False
    )

# make the package:
# python3 setup.py sdist bdist_wheel
# upload it:
# python3 -m twine upload dist/*version*

# Release:
# git tag -a v*version* -m "annotation for this release"
# git push origin --tags


# Install on nancep
# /usr/local/bin/pip3.5 install nenupytf --install-option=--prefix=/cep/lofar/nenupytf --upgrade
