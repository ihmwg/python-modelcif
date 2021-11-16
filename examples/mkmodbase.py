# Proof of concept: should generate an mmCIF file of a ModBase model,
# similar to that which can be downloaded from
# https://modbase.compbio.ucsf.edu/modbase-cgi/model_search.cgi?databaseID=Q12321
import ihm
import ihm.location
import ihm.dataset
import ihm.representation
import ihm.restraint
import ihm.protocol
import ihm.model
import ihm.dumper
import ihm.citations
import ihm.reference

system = ihm.System(title='S54091 hypothetical protein YPR070w')

modpipe_software = ihm.Software(
    name='ModPipe', classification='comparative modeling',
    location='https://salilab.org/modpipe/', type='program',
    version='SVN.r1703', description='Comparative modeling pipeline')
system.software.append(modpipe_software)

s = ihm.reference.PDBSequence(db_code='3nc1', sequence='DMACDTFIK')
template_e = ihm.Entity('DMACDTFIK', description='Template subunit',
                        references=[s])
system.entities.append(template_e)

s = ihm.reference.UniProtSequence(db_code='MED1_YEAST', accession='Q12321',
                                  sequence='DSYVETLD')
model_e = ihm.Entity('DSYVETLD', description='Model subunit',
                     references=[s])
system.entities.append(model_e)

asymA = ihm.AsymUnit(model_e, details='Model subunit A')
system.asym_units.append(asymA)

modeled_assembly = ihm.Assembly((asymA,), name='Modeled assembly')

rep = ihm.representation.Representation(
    [ihm.representation.AtomicSegment(asymA, rigid=False)])

protocol = ihm.protocol.Protocol(name='Modeling')
#protocol.steps.append(ihm.protocol.Step(
#    method='template search', name='ModPipe Seq-Prf (0001)',
#    software=x, input_data=y, output_data=z))

atoms = [('A', 1, 'C', 'CA', 1., 2., 3.),
         ('A', 2, 'C', 'CA', 4., 5., 6.),
         ('A', 3, 'C', 'CA', 7., 8., 9.)]


# Rather than storing another copy of the coordinates in the IHM library
# (which could use a lot of memory), we need to provide a mechanism to
# translate them into the IHM data model. We do this straighforwardly by
# subclassing the IHM Model class and overriding the get_atoms
# and get_spheres methods:
class MyModel(ihm.model.Model):
    # Map our asym unit names to IHM asym_unit objects:
    asym_unit_map = {'A': asymA}

    def get_atoms(self):
        for asym, seq_id, type_symbol, atom_id, x, y, z in atoms:
            yield ihm.model.Atom(asym_unit=self.asym_unit_map[asym],
                                 type_symbol=type_symbol, seq_id=seq_id,
                                 atom_id=atom_id, x=x, y=y, z=z)


model = MyModel(assembly=modeled_assembly, protocol=protocol,
                representation=rep, name='Best scoring model')

# Quality scores, todo

# Similar models can be grouped together. Here we only have a single model
# in the group
model_group = ihm.model.ModelGroup([model], name='All models')

# Groups are then placed into states, which can in turn be grouped. In this
# case we have only a single state:
state = ihm.model.State([model_group])
system.state_groups.append(ihm.model.StateGroup([state]))

# Once the system is complete, we can write it out to an mmCIF file:
with open('output.cif', 'w') as fh:
    ihm.dumper.write(fh, [system])
