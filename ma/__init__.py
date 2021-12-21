import itertools
import ihm
from ihm import AsymUnit, Software, Assembly, _remove_identical  # noqa: F401
import ma.data


class System(ihm._SystemBase):
    def __init__(self, title=None, id='model'):
        ihm._SystemBase.__init__(self, title, id)

        #: All model groups (collections of models).
        #: See :class:`~ma.model.ModelGroup`.
        self.model_groups = []

        #: All modeling protocols.
        #: See :class:`~ma.protocol.Protocol`.
        self.protocols = []

        #: All modeling alignments.
        self.alignments = []

        self.target_entities = []
        self.templates = []
        self.template_segments = []
        self.template_transformations = []
        self.data = []
        self.data_groups = []

    def _before_write(self):
        # Populate flat lists to contain all referenced objects only once
        # We must populate these in the correct order to get all objects
        self.alignments = list(_remove_identical(self.alignments))
        self.template_segments = list(
            _remove_identical(self._all_template_segments()))
        self.templates = list(_remove_identical(self._all_templates()))
        self.template_transformations = list(_remove_identical(
            self._all_template_transformations()))
        self.target_entities = list(_remove_identical(
            self._all_target_entities()))
        self.data = list(_remove_identical(
            self._all_data()))
        self.data_groups = list(_remove_identical(
            self._all_data_groups()))
        self.model_groups = list(_remove_identical(self.model_groups))

    def _check_after_write(self):
        pass

    def _all_template_segments(self):
        return itertools.chain(
            self.template_segments,
            (p.template for aln in self.alignments for p in aln.pairs))

    def _all_templates(self):
        return itertools.chain(
            self.templates,
            (x.template for x in self.template_segments))

    def _all_template_transformations(self):
        return itertools.chain(
            self.template_transformations,
            (x.transformation for x in self.templates))

    def _all_citations(self):
        """Iterate over all Citations in the system.
           This includes all Citations referenced from other objects, plus
           any referenced from the top-level system.
           Duplicates are filtered out."""
        return _remove_identical(itertools.chain(
            self.citations,
            (software.citation for software in self._all_software()
             if software.citation)))

    def _all_target_entities(self):
        """Iterate over all Entities that are used for targets rather than
           templates."""
        return (itertools.chain(
            self.target_entities,
            (asym.entity for asmb in self._all_assemblies() for asym in asmb)))

    def _all_software(self):
        """Iterate over all Software in the system.
           This includes all Software referenced from other objects, plus
           any referenced from the top-level system.
           Duplicates may be present."""
        return (itertools.chain(
            self.software))

    def _all_starting_models(self):
        return []

    def _all_entity_ranges(self):
        """Iterate over all Entity ranges in the system (these may be
           :class:`Entity`, :class:`AsymUnit`, :class:`EntityRange` or
           :class:`AsymUnitRange` objects).
           Note that we don't include self.entities or self.asym_units here,
           as we only want ranges that were actually used.
           Duplicates may be present."""
        return (itertools.chain(
            (comp for a in self._all_assemblies() for comp in a)))

    def _all_assemblies(self):
        """Iterate over all Assemblies in the system.
           This includes all Assemblies referenced from other objects, plus
           any orphaned Assemblies. Duplicates may be present."""
        return itertools.chain(
            # Complete assembly is always first
            (self.complete_assembly,),
            self.orphan_assemblies,
            (model.assembly for group, model in self._all_models()
             if model.assembly))

    def _all_model_groups(self, only_in_states=True):
        return self.model_groups

    def _all_data(self):
        return itertools.chain(
            self.data,
            self.templates,
            self.target_entities,
            self.alignments,
            (model for group, model in self._all_models()))

    def _all_data_groups(self):
        """Return all DataGroup (or singleton Data) objects"""
        return itertools.chain(
            self.data_groups,
            (step.input_data for p in self.protocols for step in p.steps),
            (step.output_data for p in self.protocols for step in p.steps))

    def _all_software_and_groups(self):
        """Return all SoftwareGroup (or singleton Software) objects"""
        return itertools.chain(
            (aln.software for aln in self.alignments if aln.software),
            (step.software for p in self.protocols for step in p.steps
             if step.software),
            (metric.software for group, model in self._all_models()
             for metric in model.qa_metrics if metric.software))


class Entity(ihm.Entity, ma.data.Data):
    # Technically only target entities have a data_id (for templates, the
    # data_id is attached to the Template object, which roughly corresponds
    # to a target AsymUnit). Rather than have a separate TargetEntity and
    # TemplateEntity (which would cause issues if they were confused, or if
    # target=template) we just don't use the data_id for template entities.
    data_content_type = "target"

    def __init__(self, sequence, alphabet=ihm.LPeptideAlphabet,
                 description=None, details=None, source=None, references=[]):
        ihm.Entity.__init__(self, sequence=sequence, alphabet=alphabet,
                            description=description, details=details,
                            source=source, references=references)
        ma.data.Data.__init__(self, name=description)


class SoftwareGroup(tuple):
    pass


class Transformation(object):
    """Rotation and translation applied to an object.

       These objects are generally used to record the transformation that
       was applied to a :class:`Template` to generate the starting structure
       used in modeling.

       :param rot_matrix: Rotation matrix (as a 3x3 array of floats) that
              places the object in its final position.
       :param tr_vector: Translation vector (as a 3-element float list) that
              places the object in its final position.
    """
    def __init__(self, rot_matrix, tr_vector):
        self.rot_matrix, self.tr_vector = rot_matrix, tr_vector

    """Return the identity transformation.

       :return: A new identity Transformation.
       :rtype: :class:`Transformation`
    """
    @classmethod
    def identity(cls):
        # todo: cache, so as not to create copies
        return cls([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]], [0., 0., 0.])


class TemplateSegment(object):
    def __init__(self, template, gapped_sequence, seq_id_begin, seq_id_end):
        self.template = template
        self.gapped_sequence = gapped_sequence
        self.seq_id_range = (seq_id_begin, seq_id_end)


class Template(ma.data.Data):
    data_content_type = "template structure"

    def __init__(self, entity, asym_id, model_num, transformation,
                 name=None, references=[]):
        super(Template, self).__init__(name)
        self.entity = entity
        self.asym_id, self.model_num = asym_id, model_num
        self.transformation = transformation
        self.references = references

    def segment(self, gapped_sequence, seq_id_begin, seq_id_end):
        # todo: cache so we return the same object for same parameters
        return TemplateSegment(self, gapped_sequence, seq_id_begin, seq_id_end)

    seq_id_range = property(lambda self: self.entity.seq_id_range,
                            doc="Sequence range")
    template = property(lambda self: self)
