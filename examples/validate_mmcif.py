# This example demonstrates the use of the Python IHM library's validator
# to validate a user-provided input mmCIF file.
# This example requires Python 3. See validate_modbase.py for a more
# detailed example that also works with Python 2.

import sys
import ihm.dictionary
import urllib.request


if len(sys.argv) != 2:
    print("Usage: %s input.cif" % sys.argv[0], file=sys.stderr)
    sys.exit(1)
fname = sys.argv[1]

# Read in the ModelCIF and PDBx dictionary from https://mmcif.wwpdb.org/
with urllib.request.urlopen(
        'https://mmcif.wwpdb.org/dictionaries/ascii/mmcif_ma.dic') as fh:
    pdbx_mcif = ihm.dictionary.read(fh)

# Validate the mmCIF file assuming it is UTF8 encoded.
# See validate_modbase.py for code to fallback to ASCII for non-UTF8 files.
with open(fname, encoding='UTF-8') as fh:
    pdbx_mcif.validate(fh)

# Similarly, to validate a BinaryCIF file, use:
# with open(fname, 'rb') as fh:
#    pdbx_mcif.validate(fh, format='BCIF')
