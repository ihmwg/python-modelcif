# Proof of concept: should generate an mmCIF file of a ModBase model,
# similar to that which can be downloaded from
# https://modbase.compbio.ucsf.edu/modbase-cgi/model_search.cgi?databaseID=Q12321
import ma
import ma.protocol
import ma.model
import ma.dumper
import ma.reference
import ma.citations

system = ma.System(title='S54091 hypothetical protein YPR070w')

system.authors.extend(('Pieper U', 'Webb B', 'Narayanan E', 'Sali A'))

modpipe_software = ma.Software(
    name='ModPipe', classification='comparative modeling',
    location='https://salilab.org/modpipe/', type='program',
    version='SVN.r1703', description='Comparative modeling pipeline')
system.software.append(modpipe_software)

modeller_software = ma.Software(
    name='MODELLER', classification='comparative modeling',
    location='https://salilab.org/modeller/', type='program',
    version='SVN', citation=ma.citations.modeller,
    description='Comparative modeling by satisfaction of spatial restraints')
system.software.append(modeller_software)

s = ma.reference.PDBSequence(db_code='3nc1', sequence='DMACDTFIK')
template_e = ma.Entity('DMACDTFIK', description='Template subunit',
                        references=[s])
system.entities.append(template_e)

s = ma.reference.UniProtSequence(db_code='MED1_YEAST', accession='Q12321',
                                 sequence='DSYVETLD')
model_e = ma.Entity('DSYVETLD', description='Model subunit',
                    references=[s])
system.entities.append(model_e)

asymA = ma.AsymUnit(model_e, details='Model subunit A')
system.asym_units.append(asymA)

modeled_assembly = ma.Assembly((asymA,), name='Modeled assembly')

protocol = ma.protocol.Protocol()
protocol.steps.append(ma.protocol.TemplateSearchStep(
    name='ModPipe Seq-Prf (0001)', software=modpipe_software))
#   input_data=y, output_data=z))
protocol.steps.append(ma.protocol.ModelingStep(software=modeller_software))
protocol.steps.append(ma.protocol.ModelSelectionStep(
    software=modpipe_software))
system.protocols.append(protocol)

atoms = [('A', 1, 'C', 'CA', 1., 2., 3.),
         ('A', 2, 'C', 'CA', 4., 5., 6.),
         ('A', 3, 'C', 'CA', 7., 8., 9.)]


# Rather than storing another copy of the coordinates in the MA library
# (which could use a lot of memory), we need to provide a mechanism to
# translate them into the MA data model. We do this straighforwardly by
# subclassing the MA Model class and overriding the get_atoms
# and get_spheres methods:
class MyModel(ma.model.Model):
    # Map our asym unit names to MA asym_unit objects:
    asym_unit_map = {'A': asymA}

    def get_atoms(self):
        for asym, seq_id, type_symbol, atom_id, x, y, z in atoms:
            yield ma.model.Atom(asym_unit=self.asym_unit_map[asym],
                                type_symbol=type_symbol, seq_id=seq_id,
                                atom_id=atom_id, x=x, y=y, z=z)


model = MyModel(assembly=modeled_assembly, name='Best scoring model')

# Quality scores, todo

# Similar models can be grouped together. Here we only have a single model
# in the group
model_group = ma.model.ModelGroup([model], name='All models')
system.model_groups.append(model_group)

# Once the system is complete, we can write it out to an mmCIF file:
with open('output.cif', 'w') as fh:
    ma.dumper.write(fh, [system])
