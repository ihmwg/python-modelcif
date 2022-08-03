import itertools
from ihm import Entity, AsymUnit, Software, Assembly, Residue  # noqa: F401
from ihm import AsymUnitRange, _remove_identical  # noqa: F401
import modelcif.data
import sys

__version__ = '0.6'


class System(object):
    """Top-level class representing a complete modeled system.

       :param str title: Longer text description of the system.
       :param str id: Unique identifier for this system in the mmCIF file.
       :param database: If this system is part of an official database
              (e.g. SwissModel, ModBase), details of the database identifiers.
       :type database: :class:`Database`
       :param str model_details: Detailed description of the system, like an
                                 abstract.

       The system contains a number of simple flat lists of various objects,
       for example :attr:`alignments`. After constructing objects they should
       usually be added to these lists so that a hierarchy of classes is
       formed and is ultimately written out to mmCIF/BinaryCIF. After reading
       a file the resulting ``System`` object will also populate these lists.

       Most objects do not need to be explicitly added to the system since
       they are referenced by other objects. For example :class:`Template`
       objects are not usually added to the system because they are added
       to alignments which in turn are added to the system. If however an
       "orphan" Template is desired (not part of an alignment) the system does
       maintain an appropriate list (``System.templates`` in this case) to
       which it can be added.
    """

    structure_determination_methodology = "computational"

    def __init__(self, title=None, id='model', database=None,
                 model_details=None):
        self.id, self.title = id, title
        self.database = database
        self.model_details = model_details

        #: List of plain text comments. These will be added to the top of
        #: the mmCIF file.
        self.comments = []

        #: List of all authors of this system, as a list of strings (last name
        #: followed by initials, e.g. "Smith AJ"). When writing out a file,
        #: if this list is empty, all authors from the first citation
        #: (see :attr:`citations` and :class:`ihm.Citation`) are used instead.
        self.authors = []

        #: List of all grants that supported this work. See :class:`ihm.Grant`.
        self.grants = []

        #: List of all citations. By convention the first citation describes
        #: the system itself. See :class:`ihm.Citation`.
        self.citations = []

        #: All groups of models. See :class:`~modelcif.model.ModelGroup`.
        self.model_groups = []

        #: All modeling protocols.
        #: See :class:`~modelcif.protocol.Protocol`.
        self.protocols = []

        #: All modeling alignments.
        #: See :mod:`modelcif.alignment`.
        self.alignments = []

        #: Any additional files with extra data about this system.
        #: See :class:`modelcif.associated.Repository`.
        self.repositories = []

        self.entities = []
        self.asym_units = []
        self.target_entities = []
        self.templates = []
        self.template_segments = []
        self.template_transformations = []
        self.data = []
        self.data_groups = []
        self.software = []
        self.software_groups = []
        self.assemblies = []

    def _all_models(self):
        """Iterate over all Models in the system"""
        # todo: raise an error if a model is present in multiple groups?
        seen_models = set()
        for group in self._all_model_groups():
            for model in group:
                if model in seen_models:
                    continue
                seen_models.add(model)
                yield group, model

    def _before_write(self):
        # Populate flat lists to contain all referenced objects only once
        # We must populate these in the correct order to get all objects
        self.assemblies = list(_remove_identical(self._all_assemblies()))
        self.asym_units = list(_remove_identical(self._all_asym_units()))
        self.alignments = list(_remove_identical(self.alignments))
        self.template_segments = list(
            _remove_identical(self._all_template_segments()))
        self.templates = list(_remove_identical(self._all_templates()))
        self.entities = list(_remove_identical(self._all_entities()))
        self.template_transformations = list(_remove_identical(
            self._all_template_transformations()))
        self.target_entities = list(_remove_identical(
            self._all_target_entities()))
        self.data_groups = list(_remove_identical(
            self._all_data_groups()))
        self.data = list(_remove_identical(
            self._all_data()))
        self.model_groups = list(_remove_identical(self.model_groups))
        self.software_groups = list(_remove_identical(
            self._all_software_groups()))
        self.software = list(_remove_identical(
            self._all_ref_software()))

    def _check_after_write(self):
        pass

    def _all_template_segments(self):
        return itertools.chain(
            self.template_segments,
            (p.template for aln in self.alignments for p in aln.pairs))

    def _all_templates(self):
        return itertools.chain(
            self.templates,
            (x.template for x in self.template_segments),
            (x.template for x in self.asym_units
             if isinstance(x, NonPolymerFromTemplate)))

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
        """Utility method used by ihm.dumper to get all Software. To initially
           populate this list from all Software referenced in the system,
           use _all_ref_software() instead."""
        return self.software

    def _all_ref_software(self):
        """Iterate over all Software in the system.
           This includes all Software referenced from other objects, plus
           any referenced from the top-level system.
           Duplicates may be present."""
        def _all_software_in_groups():
            for sg in self.software_groups:
                if isinstance(sg, Software):
                    yield sg
                else:
                    for s in sg:
                        yield s

        def _all_entities():
            return itertools.chain(
                self.entities, (t.entity for t in self.templates))

        def _all_descriptor_software():
            comps = frozenset(comp for e in _all_entities()
                              for comp in e.sequence)
            for comp in comps:
                if hasattr(comp, 'descriptors') and comp.descriptors:
                    for desc in comp.descriptors:
                        if desc.software:
                            yield desc.software
        return (itertools.chain(
            self.software, _all_software_in_groups(),
            _all_descriptor_software()))

    def _all_assemblies(self):
        """Iterate over all Assemblies in the system.
           This includes all Assemblies referenced from other objects, plus
           any orphaned Assemblies. Duplicates may be present."""
        return itertools.chain(
            self.assemblies,
            (model.assembly for group, model in self._all_models()
             if model.assembly))

    def _all_asym_units(self):
        def _all_asym_in_assemblies():
            for asmb in self.assemblies:
                for a in asmb:
                    yield a.asym if hasattr(a, 'asym') else a
        return itertools.chain(
            self.asym_units, _all_asym_in_assemblies())

    def _all_entities(self):
        # Note that template entities are not included by default
        return itertools.chain(
            self.entities,
            (asym.entity for asym in self.asym_units))

    def _all_model_groups(self, only_in_states=True):
        return self.model_groups

    def _all_data(self):
        def _all_data_in_groups():
            for dg in self.data_groups:
                if isinstance(dg, list):
                    for data in dg:
                        yield data
        return itertools.chain(
            self.data,
            self.templates,
            self.target_entities,
            self.alignments,
            (model for group, model in self._all_models()),
            _all_data_in_groups())

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


# Provide ma-specific docs for Entity
if sys.version_info[0] >= 3:
    Entity.__doc__ = """Represent a unique molecular sequence.

This can be used both for template sequences (in which case the Entity is
then used in a :class:`Template` object) or for target (model) sequences
(where it is used in a :class:`AsymUnit` object).

(Note that template sequence Entity objects are not written out to the
entity, entity_poly etc. tables in the mmCIF/BinaryCIF file by default.
Instead, sequence information is captured in template-specific categories.)

:param sequence sequence: The primary sequence, as a sequence of
       :class:`ihm.ChemComp` objects, and/or codes looked up in `alphabet`.
       See `ihm.Entity <https://python-ihm.readthedocs.io/en/latest/main.html#ihm.Entity>`_ for examples.
:param alphabet: The mapping from code to chemical components to use
       (it is not necessary to instantiate this class).
:type alphabet: :class:`ihm.Alphabet`
:param str description: A short text name for the sequence.
:param str details: Longer text describing the sequence.
:param source: The method by which the sample for this entity was produced.
:type source: :class:`ihm.source.Source`
:param references: For a target (model) sequence, information about this
       entity stored in external databases (for example the sequence in
       UniProt). For references to structure databases for templates,
       see :class:`Template` instead.
:type references: sequence of :class:`reference.TargetReference` objects

See `ihm.Entity <https://python-ihm.readthedocs.io/en/latest/main.html#ihm.Entity>`_ for more information.
"""  # noqa: E501


# Provide ma-specific docs for Software
if sys.version_info[0] >= 3:
    Software.__doc__ = """Software used as part of the modeling protocol.

:param str name: The name of the software.
:param str classification: The major function of the sofware, for
       example 'model building', 'sample preparation', 'data collection'.
:param str description: A longer text description of the software.
:param str location: Place where the software can be found (e.g. URL).
:param str type: Type of software (program/package/library/other).
:param str version: The version used.
:param citation: Publication describing the software.
:type citation: :class:`ihm.Citation`

Generally these objects are added to groups (see :class:`SoftwareGroup`)
which can then be used to describe the software used in various parts of the
modeling (``Software`` objects can also be used any place
:class:`SoftwareGroup` are accepted, in which case they will act as if a group
containing only a single member was used).

See also :attr:`System.software`.
"""

# Provide ma-specific docs for Assembly
if sys.version_info[0] >= 3:
    Assembly.__doc__ = """A collection of parts of the system that were modeled
together.

:param sequence elements: Initial set of parts of the system.
:param str name: Short text name of this assembly.
:param str description: Longer text that describes this assembly.

This is implemented as a simple list of asymmetric units (or parts of
them), i.e. a list of :class:`AsymUnit` and/or :class:`AsymUnitRange`
objects. An Assembly is typically passed to the :class:`modelcif.model.Model`
constructor.

Note that the ModelCIF dictionary has deprecated the corresponding
``ma_struct_assembly`` category, so any name or description of the assembly
will not be written to the mmCIF file. The ModelCIF dictionary requires that
all models have the same composition.
"""


class Database(object):
    """Information about a System that is part of an official database.

       If a :class:`System` is part of an official database (e.g. SwissModel,
       ModBase), this class contains details of the database identifiers.
       It should be passed to the :class:`System` constructor.

       :param str id: Abbreviated name of the database (e.g. PDB)
       :param str code: Identifier from the database (e.g. 1abc)
       """
    def __init__(self, id, code):
        self.id, self.code = id, code


class SoftwareGroup(list):
    """A number of :class:`Software` objects that are grouped together.

       This class can be used to group together multiple :class:`Software`
       objects if multiple pieces of software were used together to generate
       a single alignment (see :class:`modelcif.alignment.AlignmentMode`), to
       run a modeling step (see :class:`modelcif.protocol.Step`), or to
       calculate a model quality score (see :mod:`modelcif.qa_metric`).
       It behaves like a regular Python list.

       :param sequence elements: Initial set of :class:`Software` objects.
       :param parameters: All parameters input to this software group.
       :type parameters: sequence of :class:`SoftwareParameter`
    """

    def __init__(self, elements=(), parameters=None):
        super(SoftwareGroup, self).__init__(elements)
        self.parameters = [] if parameters is None else parameters


class SoftwareParameter(object):
    """A single parameter given to software used in modeling.

       See :class:`SoftwareGroup`.

       :param str name: A short name for this parameter.
       :param value: Parameter value.
       :type value: ``int``, ``float``, ``str``, ``bool``, list of ``int``,
             or list of ``float``.
       :param str description: A longer description of the parameter.
    """
    def __init__(self, name, value, description=None):
        self.name, self.value = name, value
        self.description = description

    def __repr__(self):
        return ("<SoftwareParameter(name=%r, value=%r)>"
                % (self.name, self.value))


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
        if not hasattr(cls, '_identity_obj'):
            cls._identity_obj = cls(
                [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]], [0., 0., 0.])
        return cls._identity_obj


class TemplateSegment(object):
    """An aligned part of a template (see :class:`modelcif.alignment.Pair`).

       Usually these objects are created from
       a :class:`Template` using :meth:`Template.segment`, e.g. to get a
       segment covering residues 1 through 3 in `tmpl` use::

           tmpl = modelcif.Template(entity, ...)
           seg = tmpl.segment('--ACG', 1, 3)
    """
    def __init__(self, template, gapped_sequence, seq_id_begin, seq_id_end):
        self.template = template
        self.gapped_sequence = gapped_sequence
        self.seq_id_range = (seq_id_begin, seq_id_end)


class Template(modelcif.data.Data):
    """A single chain that was used as a template structure for modeling.

       After creating a polymer template, use :meth:`segment` to denote the
       part of its sequence used in any modeling alignments
       (see :class:`modelcif.alignment.Pair`).

       Non-polymer templates do not have alignments, and should instead be
       passed to one or more :class:`NonPolymerFromTemplate` objects.

       Template objects can also be used as inputs or outputs in modeling
       protocol steps; see :class:`modelcif.protocol.Step`.

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
       :type references: list of :class:`modelcif.reference.TemplateReference`
             objects
       :param str strand_id: PDB or "author-provided" strand/chain ID.
              If not specified, it will be the same as the regular asym_id.
       :param str entity_id: If known, the ID of the entity for this template
              in its own mmCIF file.
    """
    data_content_type = "template structure"

    def __init__(self, entity, asym_id, model_num, transformation,
                 name=None, references=[], strand_id=None, entity_id=None):
        super(Template, self).__init__(name)
        self.entity = entity
        self.asym_id, self.model_num = asym_id, model_num
        self.transformation = transformation
        self.references = []
        self.references.extend(references)
        self._strand_id = strand_id
        self.entity_id = entity_id

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

    strand_id = property(lambda self: self._strand_id or self.asym_id,
                         doc="PDB or author-provided strand/chain ID")


class NonPolymerFromTemplate(AsymUnit):
    """A non-polymer (e.g. ligand) in the model that is modeled from
       a non-polymer template.

       These objects act just like :class:`AsymUnit` and should be added
       to :class:`Assembly`.

       To represent a non-polymer that is modeled without a template, just
       use a regular :class:`AsymUnit`.

       :param template: The non-polymer template used to model
              this non-polymer.
       :type template: :class:`Template`
       :param bool explicit: True iff the conformation of the template is
              allowed to change (e.g. bond relaxation, flexible fitting)
              during the modeling, or False if the template is treated as
              a single rigid body.

       For the other parameters, see :class:`AsymUnit`.
    """

    def __init__(self, template, explicit, details=None, auth_seq_id_map=0,
                 id=None, strand_id=None):
        super(NonPolymerFromTemplate, self).__init__(
            template.entity, details=details, auth_seq_id_map=auth_seq_id_map,
            id=id, strand_id=strand_id)
        self.template, self.explicit = template, explicit


class ReferenceDatabase(modelcif.data.Data):
    """A reference database used in the modeling. This is typically a
       sequence database used for template search, alignments, etc.
       These objects are passed as input or output to
       :class:`modelcif.protocol.Step`. See also :class:`modelcif.data.Data`
       for more details.

       Compare with :class:`modelcif.reference.TargetReference`, which pertains
       to just the modeled sequence itself; this class describes *multiple*
       sequences.

       :param str name: Name of the database.
       :param str url: Location of the database.
       :param str version: Version of the database.
       :param release_date: Release date of the specified version.
       :type release_date: :class:`datetime.date`
    """
    data_content_type = "reference database"

    def __init__(self, name, url, version=None, release_date=None):
        super(ReferenceDatabase, self).__init__(name)
        self.url, self.version, self.release_date = url, version, release_date
