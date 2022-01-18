import itertools
from ihm import Entity, AsymUnit, Software, Assembly  # noqa: F401
from ihm import AsymUnitRange, _remove_identical  # noqa: F401
import ma.data

__version__ = '0.1'


class System(object):
    """Top-level class representing a complete modeled system.

       :param str title: Longer text description of the system.
       :param str id: Unique identifier for this system in the mmCIF file.
    """

    def __init__(self, title=None, id='model'):
        self.id, self.title = id, title

        #: List of plain text comments. These will be added to the top of
        #: the mmCIF file.
        self.comments = []

        #: List of all software used in the modeling. See :class:`Software`.
        self.software = []

        #: List of all authors of this system, as a list of strings (last name
        #: followed by initials, e.g. "Smith AJ"). When writing out a file,
        #: if this list is empty, the set of all citation authors (see
        #: :attr:`Citation.authors`) is used instead.
        self.authors = []

        #: List of all grants that supported this work. See :class:`Grant`.
        self.grants = []

        #: List of all citations. See :class:`Citation`.
        self.citations = []

        #: All entities used in the system. See :class:`Entity`.
        self.entities = []

        #: All asymmetric units used in the system. See :class:`AsymUnit`.
        self.asym_units = []

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
        self.software_groups = []
        self.assemblies = []

    def _all_models(self):
        """Iterate over all Models in the system"""
        # todo: raise an error if a model is present in multiple groups
        for group in self._all_model_groups():
            seen_models = {}
            for model in group:
                if model in seen_models:
                    continue
                seen_models[model] = None
                yield group, model

    def _before_write(self):
        # Populate flat lists to contain all referenced objects only once
        # We must populate these in the correct order to get all objects
        self.assemblies = list(_remove_identical(self._all_assemblies()))
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
        self.software_groups = list(_remove_identical(
            self._all_software_groups()))

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
            (asym.entity for asmb in self.assemblies for asym in asmb)))

    def _all_software(self):
        """Iterate over all Software in the system.
           This includes all Software referenced from other objects, plus
           any referenced from the top-level system.
           Duplicates may be present."""
        return (itertools.chain(
            self.software))

    def _all_assemblies(self):
        """Iterate over all Assemblies in the system.
           This includes all Assemblies referenced from other objects, plus
           any orphaned Assemblies. Duplicates may be present."""
        return itertools.chain(
            self.assemblies,
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

    def _all_software_groups(self):
        """Return all SoftwareGroup (or singleton Software) objects"""
        return itertools.chain(
            self.software_groups,
            (aln.software for aln in self.alignments if aln.software),
            (step.software for p in self.protocols for step in p.steps
             if step.software),
            (metric.software for group, model in self._all_models()
             for metric in model.qa_metrics if metric.software))


class SoftwareGroup(list):
    """A number of :class:`Software` objects that are grouped together.

       This class can be used to group together multiple :class:`Software`
       objects if multiple pieces of software were used together to generate
       a single alignment (see :class:`ma.alignment.AlignmentMode`) or to
       run a modeling step (see :class:`ma.protocol.Step`).
       It behaves like a regular Python list.
    """
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
    """An aligned part of a template (see :class:`ma.alignment.Pair`).

       Usually these objects are created from
       a :class:`Template` using :meth:`Template.segment`, e.g. to get a
       segment covering residues 1 through 3 in `tmpl` use::

           tmpl = ma.Template(entity, ...)
           seg = tmpl.segment('--ACG', 1, 3)
    """
    def __init__(self, template, gapped_sequence, seq_id_begin, seq_id_end):
        self.template = template
        self.gapped_sequence = gapped_sequence
        self.seq_id_range = (seq_id_begin, seq_id_end)


class Template(ma.data.Data):
    """A single chain that was used as a template structure for modeling.

       After creating a template, use :meth:`segment` to denote the part of
       its sequence used in any modeling alignments
       (see :class:`ma.alignment.Pair`).
       Template objects can also be used as inputs or outputs in modeling
       protocol steps; see :class:`ma.protocol.Step`.

       :param entity: The sequence of the chain.
       :type entity: :class:`Entity`
       :param str asym_id: The asym or chain ID in the template structure.
       :param int model_num: The model number of the template structure.
       :param transformation: Rotation and translation applied to the original
              template structure to get the starting model used in modeling.
       :type transformation: :class:`Transformation`
       :param str name: A short name for this template.
       :param references: A list of pointers to reference databases (such as
              PDB) from which the template structure was taken.
       :type references: list of :class:`ma.reference.TemplateReference`
             objects
    """
    data_content_type = "template structure"

    def __init__(self, entity, asym_id, model_num, transformation,
                 name=None, references=[]):
        super(Template, self).__init__(name)
        self.entity = entity
        self.asym_id, self.model_num = asym_id, model_num
        self.transformation = transformation
        self.references = []
        self.references.extend(references)

    def segment(self, gapped_sequence, seq_id_begin, seq_id_end):
        """Get an object representing the alignment of part of this sequence.

           :param str gapped_sequence: Sequence of the segment, including gaps.
           :param int seq_id_begin: Start of the segment.
           :param int seq_id_end: End of the segment.
        """
        # todo: cache so we return the same object for same parameters
        return TemplateSegment(self, gapped_sequence, seq_id_begin, seq_id_end)

    seq_id_range = property(lambda self: self.entity.seq_id_range,
                            doc="Sequence range")
    template = property(lambda self: self)
