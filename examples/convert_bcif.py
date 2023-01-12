# This example demonstrates using the library to convert an mmCIF file
# containing ModelCIF data to BinaryCIF format.

# Import used classes.
import modelcif
import modelcif.dumper
import modelcif.reader

# Read in an existing mmCIF file:
with open('input/ligands.cif') as fh:
    systems = modelcif.reader.read(fh, format='mmCIF')

# Write a new BinaryCIF file containing the same data:
with open('ligands.bcif', 'wb') as fh:
    modelcif.dumper.write(fh, systems, format='BCIF')
