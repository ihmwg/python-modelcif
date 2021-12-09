import itertools
import ihm
from ihm import Entity, Software, AsymUnit, Assembly, _remove_identical


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

    def _before_write(self):
        pass

    def _check_after_write(self):
        pass

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


class SoftwareGroup(tuple):
    pass
