# This example demonstrates writing an mmCIF file of a typical
# single-template homology or comparative model, including a ligand.
#
# This is very similar to the mkmodbase.py example; see that example for
# more details.

# Import used classes
import modelcif
import modelcif.model
import modelcif.dumper
import modelcif.reference
import modelcif.protocol
import modelcif.alignment
from modelcif.alignment import ShorterSequenceIdentity as SequenceIdentity
import ihm

system = modelcif.System(title='Ligand example')

# Describe the amino acid (polymer) sequences as Entity objects, for both
# template and model:
template_e = modelcif.Entity('AFVVTDNCIKCK', description='Template subunit')
model_e = modelcif.Entity('AYVINDSCIA', description='Model subunit')

# For non-polymers (e.g. ligands) we need to describe the chemistry of the
# ligand as a chemical component object, then create an Entity using that
# component. We only need to do this once because the ligand is the same
# in both template and model:
sf4 = ihm.NonPolymerChemComp("SF4", name='IRON/SULFUR CLUSTER',
                             formula='Fe4 S4')
ligand_e = modelcif.Entity([sf4], description='IRON/SULFUR CLUSTER')

# Create a Template for each chain (amino acids in chain A, ligand in chain B)
# and point to the original PDB, 5fd1:
s = modelcif.reference.PDB('5fd1')
templateA = modelcif.Template(
    entity=template_e, asym_id='A', model_num=1, name="Template polymer",
    transformation=modelcif.Transformation.identity(), references=[s])
templateB = modelcif.Template(
    entity=ligand_e, asym_id='B', model_num=1, name='Template ligand',
    transformation=modelcif.Transformation.identity(), references=[s])

# Define the model assembly, as two AsymUnits. NonPolymerFromTemplate is a
# subclass of AsymUnit that additionally notes the Template from which it
# was derived. In this case we state that the ligand was simply copied from
# the template into the target (explicit=False):
asymA = modelcif.AsymUnit(model_e, details='Model subunit A', id='A')
asymB = modelcif.NonPolymerFromTemplate(template=templateB, explicit=False,
                                        details='Model subunit B', id='B')
modeled_assembly = modelcif.Assembly((asymA, asymB), name='Modeled assembly')


# For the amino acid chain, add the modeling alignment, just as in the
# mkmodbase.py example:
class Alignment(modelcif.alignment.Global, modelcif.alignment.Pairwise):
    pass


p = modelcif.alignment.Pair(
    template=templateA.segment("AFVVTDNCIKCK", 1, 12),
    target=asymA.segment("AYVINDSC--IA", 1, 10),
    score=modelcif.alignment.BLASTEValue(1e-15),
    identity=SequenceIdentity(45.0))
aln = Alignment(name="Modeling alignment",
                pairs=[p])
system.alignments.append(aln)

# Add model coordinates, similarly to the mkmodbase.py example.
# Note that nonpolymers are not "sequences" and so seq_id=None.
atoms = [('A', 1, 'C', 'CA', 1., 2., 3.),
         ('A', 2, 'C', 'CA', 4., 5., 6.),
         ('A', 3, 'C', 'CA', 7., 8., 9.),
         ('B', None, 'FE', 'FE', 10., 10., 10.)]


class MyModel(modelcif.model.HomologyModel):
    asym_unit_map = {'A': asymA, 'B': asymB}

    def get_atoms(self):
        for asym, seq_id, type_symbol, atom_id, x, y, z in atoms:
            yield modelcif.model.Atom(
                asym_unit=self.asym_unit_map[asym], type_symbol=type_symbol,
                seq_id=seq_id, atom_id=atom_id, x=x, y=y, z=z,
                het=seq_id is None)


# Add the model and modeling protocol to the file and write them out:
model = MyModel(assembly=modeled_assembly, name='Best scoring model')

model_group = modelcif.model.ModelGroup([model], name='All models')
system.model_groups.append(model_group)

protocol = modelcif.protocol.Protocol()
protocol.steps.append(modelcif.protocol.ModelingStep(
    input_data=aln, output_data=model))
system.protocols.append(protocol)

with open('output.cif', 'w') as fh:
    modelcif.dumper.write(fh, [system])
