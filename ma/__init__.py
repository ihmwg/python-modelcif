import itertools
import ihm
from ihm import Entity, Software, Assembly, _remove_identical
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

        self.templates = []
        self.template_segments = []

    def _before_write(self):
        # Populate flat lists to contain all referenced objects only once
        # We must populate these in the correct order to get all objects
        self.alignments = list(_remove_identical(self.alignments))
        self.template_segments = list(
            _remove_identical(self._all_template_segments()))
        self.templates = list(_remove_identical(self._all_templates()))

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
        return _remove_identical(itertools.chain(
            asym.entity for asmb in self._all_assemblies() for asym in asmb))

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
            self.templates,
            self.asym_units,
            self.alignments,
            (model for group, model in self._all_models()))

    def _all_data_groups(self):
        """Return all DataGroup (or singleton Data) objects"""
        return itertools.chain(
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


class TargetSegment(object):
    def __init__(self, asym, gapped_sequence, seq_id_begin, seq_id_end):
        self.asym = asym
        self.gapped_sequence = gapped_sequence
        self.seq_id_range = (seq_id_begin, seq_id_end)


class AsymUnit(ihm.AsymUnit, ma.data.Data):
    data_content_type = "target"

    def __init__(self, entity, details=None, auth_seq_id_map=0, id=None,
                 name=None):
        ihm.AsymUnit.__init__(self, entity=entity, details=details,
                              auth_seq_id_map=auth_seq_id_map, id=id)
        ma.data.Data.__init__(self, name=name)

    def segment(self, gapped_sequence, seq_id_begin, seq_id_end):
        # todo: cache so we return the same object for same parameters
        return TargetSegment(self, gapped_sequence, seq_id_begin, seq_id_end)


class SoftwareGroup(tuple):
    pass


class TemplateSegment(object):
    def __init__(self, template, gapped_sequence, seq_id_begin, seq_id_end):
        self.template = template
        self.gapped_sequence = gapped_sequence
        self.seq_id_range = (seq_id_begin, seq_id_end)


class Template(ma.data.Data):
    data_content_type = "template structure"

    def __init__(self, entity, asym_id, model_num, name=None):
        super(Template, self).__init__(name)
        self.entity = entity
        self.asym_id, self.model_num = asym_id, model_num

    def segment(self, gapped_sequence, seq_id_begin, seq_id_end):
        # todo: cache so we return the same object for same parameters
        return TemplateSegment(self, gapped_sequence, seq_id_begin, seq_id_end)

    seq_id_range = property(lambda self: self.entity.seq_id_range,
                            doc="Sequence range")
    template = property(lambda self: self)
