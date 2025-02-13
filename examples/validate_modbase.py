# This example demonstrates the use of the Python IHM library's validator.
# A structure is downloaded from the ModBase database and checked against
# the ModelCIF dictionary for compliance. This validator can be used
# to perform basic integrity checking against any mmCIF dictionary.
# See also validate_mmcif.py for a simpler script to validate a
# user-provided mmCIF file.

import io
import ihm.dictionary
import urllib.request

# Read in the ModelCIF dictionary from wwPDB as a Dictionary object.
# Note that the ModelCIF dictionary also includes the PDBx dictionary,
# so we don't need to read that in separately
fh = urllib.request.urlopen(
    'https://mmcif.wwpdb.org/dictionaries/ascii/mmcif_ma.dic')
pdbx_mc = ihm.dictionary.read(fh)
fh.close()

# Validate a structure against PDBx+ModelCIF.
# A correct structure here should result in no output; an invalid structure
# will result in a ValidatorError Python exception.
# Here, a structure from ModBase (which should be valid) is used.
acc = 'P21812'
cif = urllib.request.urlopen('https://salilab.org/modbase/retrieve'
                             '?databaseID=%s&format=mmcif' % acc).read()

# The encoding for mmCIF files isn't strictly defined, so first try UTF-8
# and if that fails, strip out any non-ASCII characters. This ensures that
# we handle accented characters in string fields correctly.
try:
    fh = io.StringIO(cif.decode('utf-8'))
except UnicodeDecodeError:
    fh = io.StringIO(cif.decode('ascii', errors='ignore'))

pdbx_mc.validate(fh)
