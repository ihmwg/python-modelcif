#!/usr/bin/env python3

"""
Add minimal ModelCIF-related tables to an mmCIF file.

Given any mmCIF file as input, this script will add any missing
ModelCIF-related tables and write out a new file that is minimally compliant
with the ModelCIF dictionary.

This is done by simply reading in the original file with python-modelcif and
then writing it out again, so
  a) any data in the input file that is not understood by python-modelcif
     will be lost on output; and
  b) input files that aren't compliant with the PDBx dictionary, or that
     contain syntax errors or other problems, may crash or otherwise confuse
     python-modelcif.

While a best effort is made, it is not guaranteed that the output file is
valid. It is recommended that it is run through a validator such as
../examples/validate_mmcif.py and any errors corrected or reported as
issues..
"""


import modelcif.reader
import modelcif.dumper
import ihm
import sys


def add_modelcif_info(s):
    if not s.title:
        s.title = 'Auto-generated system'
    if not s.protocols:
        default_protocol = modelcif.protocol.Protocol()
        step = modelcif.protocol.ModelingStep(
            name='modeling', input_data=None, output_data=None)
        default_protocol.steps.append(step)
        s.protocols.append(default_protocol)
    # Entity description is also used by python-modelcif for ma_data.name,
    # which is mandatory, so it cannot be unknown/?
    for mg in s.model_groups:
        for m in mg:
            for asym in m.assembly:
                if asym.entity.description is ihm.unknown:
                    asym.entity.description = "target"
    return s


if len(sys.argv) != 2:
    print("Usage: %s input.cif" % sys.argv[0], file=sys.stderr)
    sys.exit(1)
fname = sys.argv[1]

with open(fname) as fh:
    with open('output.cif', 'w') as fhout:
        modelcif.dumper.write(
            fhout, [add_modelcif_info(s) for s in modelcif.reader.read(fh)])
