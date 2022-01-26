# This example demonstrates the use of the Python IHM library's validator.
# A structure is downloaded from the ModBase database and checked against
# the PDBx and ModelCIF dictionaries for compliance. This validator can be used
# to perform basic integrity checking against any mmCIF dictionary.

import io
import sys
import ihm.dictionary
try:
    import urllib.request as urllib2  # Python 3
except ImportError:
    import urllib2  # Python 2

# Read in the PDBx dictionary from wwPDB as a Dictionary object
fh = urllib2.urlopen(
    'http://mmcif.wwpdb.org/dictionaries/ascii/mmcif_pdbx_v50.dic')
d_pdbx = ihm.dictionary.read(fh)
fh.close()

# Also read in the ModelCIF dictionary
fh = urllib2.urlopen('https://mmcif.wwpdb.org/dictionaries/ascii/mmcif_ma.dic')
d_mc = ihm.dictionary.read(fh)
fh.close()

# Deposited theoretical models should conform to both the PDBx dictionary
# (used to define basic structural information such as residues and chains)
# and the ModelCIF dictionary (used for information specific to theoretical
# models). Make a dictionary that combines the PDBx and ModelCIF dictionaries
# using the + operator.
pdbx_mc = d_pdbx + d_mc

# Validate a structure against PDBx+ModelCIF.
# A correct structure here should result in no output; an invalid structure
# will result in a ValidatorError Python exception.
# Here, a structure from ModBase (which should be valid) is used.
acc = 'P21812'
cif = urllib2.urlopen('https://salilab.org/modbase/retrieve'
                      '?databaseID=%s&format=mmcif' % acc).read()

# The encoding for mmCIF files isn't strictly defined, so first try UTF-8
# and if that fails, strip out any non-ASCII characters. This ensures that
# we handle accented characters in string fields correctly.
if sys.version_info[0] >= 3:
    try:
        fh = io.StringIO(cif.decode('utf-8'))
    except UnicodeDecodeError:
        fh = io.StringIO(cif.decode('ascii', errors='ignore'))
else:
    fh = io.BytesIO(cif.decode('ascii', errors='ignore').encode('ascii'))

pdbx_mc.validate(fh)
