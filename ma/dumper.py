import itertools
import ihm.dumper
from ihm import util
from ihm.dumper import Dumper, Variant, _assign_range_ids


class _AuditConformDumper(Dumper):
    URL = ("https://raw.githubusercontent.com/" +
           "ihmwg/MA-dictionary/%s/mmcif_ma.dic")

    def dump(self, system, writer):
        with writer.category("_audit_conform") as lp:
            # Update to match the version of the MA dictionary we support:
            lp.write(dict_name="mmcif_ma.dic", dict_version="1.3.3",
                     dict_location=self.URL % "8b46f31")


class _DataDumper(Dumper):
    def finalize(self, system):
        seen_data = {}
        self._data_by_id = []
        for d in system._all_data():
            util._remove_id(d, attr='_data_id')
        for d in system._all_data():
            util._assign_id(d, seen_data, self._data_by_id, attr='_data_id')

    def dump(self, system, writer):
        with writer.loop(
                "_ma_data",
                ["id", "name", "content_type",
                 "content_type_other_details"]) as lp:
            for d in self._data_by_id:
                lp.write(id=d._data_id, name=d.name,
                         content_type=d.data_content_type,
                         content_type_other_details=d.data_other_details)


class _TemplatePolySegmentDumper(Dumper):
    def finalize(self, system):
        self._ranges_by_id = []
        _assign_range_ids(system, self._ranges_by_id)

    def dump(self, system, writer):
        # todo: only output this info for templates
        with writer.loop("_ma_template_poly_segment",
                         ["id", "template_id", "residue_number_begin",
                          "residue_number_end"]) as lp:
            for rng in self._ranges_by_id:
                entity = rng.entity if hasattr(rng, 'entity') else rng
                lp.write(
                    id=rng._range_id, template_id=entity._id,
                    residue_number_begin=rng.seq_id_range[0],
                    residue_number_end=rng.seq_id_range[1])


class _AssemblyDumper(ihm.dumper._AssemblyDumperBase):
    def dump(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop("_ma_struct_assembly",
                         ["ordinal_id", "assembly_id", "entity_id", "asym_id",
                          "seq_id_begin", "seq_id_end"]) as lp:
            for a in self._assembly_by_id:
                for comp in a:
                    entity = comp.entity if hasattr(comp, 'entity') else comp
                    lp.write(
                        ordinal_id=next(ordinal), assembly_id=a._id,
                        entity_id=entity._id,
                        asym_id=comp._id if hasattr(comp, 'entity') else None,
                        seq_id_begin=comp.seq_id_range[0],
                        seq_id_end=comp.seq_id_range[1])


class _ProtocolDumper(Dumper):
    def finalize(self, system):
        # Assign IDs to protocols and steps
        for np, p in enumerate(system.protocols):
            p._id = np + 1
            for ns, s in enumerate(p.steps):
                s._id = ns + 1

    def dump(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_protocol_step",
                ['ordinal_id', 'protocol_id', 'step_id', 'method_type',
                 'step_name', 'details', 'software_group_id',
                 'input_data_group_id', 'output_data_group_id']) as lp:
            for p in system.protocols:
                for s in p.steps:
                    lp.write(ordinal_id=next(ordinal), protocol_id=p._id,
                             step_id=s._id, method_type=s.method_type,
                             step_name=s.name, details=s.details,
                             # todo: should be group id, not software id
                             software_group_id=s.software._id if s.software
                             else None,
                             input_data_group_id=s.input_data._data_id,
                             output_data_group_id=s.output_data._data_id)


class _ModelDumper(ihm.dumper._ModelDumperBase):
    def dump(self, system, writer):
        self.dump_model_list(system, writer)
        seen_types = self.dump_atoms(system, writer, add_ihm=False)
        self.dump_atom_type(seen_types, system, writer)

    def dump_model_list(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop("_ma_model_list",
                         ["ordinal_id", "model_id", "model_group_id",
                          "model_name", "model_group_name", "assembly_id",
                          "data_id", "model_type"]) as lp:
            for group, model in system._all_models():
                lp.write(ordinal_id=next(ordinal), model_id=model._id,
                         model_group_id=group._id, model_name=model.name,
                         model_group_name=group.name,
                         assembly_id=model.assembly._id,
                         data_id=model._data_id)


class ModelArchiveVariant(Variant):
    _dumpers = [
        ihm.dumper._EntryDumper,  # must be first
        ihm.dumper._StructDumper, ihm.dumper._CommentDumper,
        _AuditConformDumper, ihm.dumper._CitationDumper,
        ihm.dumper._SoftwareDumper, ihm.dumper._AuditAuthorDumper,
        ihm.dumper._GrantDumper, ihm.dumper._ChemCompDumper,
        ihm.dumper._EntityDumper,
        ihm.dumper._EntitySrcGenDumper, ihm.dumper._EntitySrcNatDumper,
        ihm.dumper._EntitySrcSynDumper, ihm.dumper._StructRefDumper,
        ihm.dumper._EntityPolyDumper, ihm.dumper._EntityNonPolyDumper,
        ihm.dumper._EntityPolySeqDumper, ihm.dumper._StructAsymDumper,
        ihm.dumper._PolySeqSchemeDumper, ihm.dumper._NonPolySchemeDumper,
        _DataDumper,
        _TemplatePolySegmentDumper, _AssemblyDumper, _ProtocolDumper,
        _ModelDumper]

    def get_dumpers(self):
        return [d() for d in self._dumpers]


def write(fh, systems, format='mmCIF', dumpers=[], variant=ModelArchiveVariant):
    return ihm.dumper.write(fh, systems, format, dumpers, variant)
