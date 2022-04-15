#!/bin/bash -e

# First, do
# - Update AuditConformDumper to match latest MA dictionary if necessary
# - Run util/validate-outputs.py to make sure all example outputs validate
# - If we need a newer python-ihm, update the version requirement in
#   requirements.txt, setup.py, and README.md.
# - Update ChangeLog.rst with the release number
# - Update release number in modelcif/__init__.py and setup.py
# - Commit, tag, and push
# - Make release on GitHub
# - Upload the release tarball from
#   https://github.com/ihmwg/python-modelcif/releases to Zenodo as a new release
# - Make sure there are no extraneous .py files (setup.py will include them
#   in the pypi package)

VERSION=$(python3 setup.py --version)
python3 setup.py sdist
echo "Now use 'twine upload dist/modelcif-${VERSION}.tar.gz' to publish the release on PyPi"
