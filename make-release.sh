#!/bin/bash -e

# First, do
# - Update ChangeLog.rst with the release number
# - Update release number in modelcif/__init__.py and setup.py
# - Commit, tag, and push
# - Make release on GitHub
# - Upload the release tarball from
#   https://github.com/ihmwg/python-modelcif/releases to Zenodo as a new release
# - Make sure there are no extraneous .py files (setup.py will include them
#   in the pypi package)

python3 setup.py sdist
echo "Now use 'twine upload dist/modelcif-${VERSION}.tar.gz' to publish the release on PyPi"
