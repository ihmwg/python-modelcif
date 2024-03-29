#!/usr/bin/python3

"""Check the output of each example for validity against the PDBx
   and ModelCIF dictionaries.

   This should be periodically rechecked in case the PDBx and ModelCIF
   dictionaries are updated.
"""

import sys
import os
import subprocess
import ihm.dictionary
import urllib.request

with urllib.request.urlopen(
        'https://mmcif.wwpdb.org/dictionaries/ascii/mmcif_ma.dic') as fh:
    pdbx_mcif = ihm.dictionary.read(fh)

for script in ('mkmodbase.py', 'ligands.py'):
    print(script)
    subprocess.check_call([sys.executable, '../examples/' + script])
    with open('output.cif') as fh:
        try:
            pdbx_mcif.validate(fh)
        except ihm.dictionary.ValidatorError as exc:
            print(exc)
os.unlink('output.cif')
