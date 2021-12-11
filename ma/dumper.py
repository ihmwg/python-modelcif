import itertools
import operator
import ihm.dumper
from ihm import util
from ihm.dumper import Dumper, Variant, _prettyprint_seq
import ma.qa_metric
import ma.data


class _AuditConformDumper(Dumper):
    URL = ("https://raw.githubusercontent.com/" +
           "ihmwg/MA-dictionary/%s/mmcif_ma.dic")

    def dump(self, system, writer):
        with writer.category("_audit_conform") as lp:
            # Update to match the version of the MA dictionary we support:
            lp.write(dict_name="mmcif_ma.dic", dict_version="1.3.3",
                     dict_location=self.URL % "8b46f31")


class _TargetRefDBDumper(Dumper):
    def dump(self, system, writer):
        entities = sorted(system._all_target_entities(),
                          key=operator.attrgetter('_id'))
        with writer.loop(
                "_ma_target_ref_db_details",
                ["target_entity_id", "db_name", "db_name_other_details",
                 "db_code", "db_accession", "seq_db_isoform",
                 "seq_db_align_begin", "seq_db_align_end"]) as lp:
            for e in entities:
                for r in e.references:
                    db_begin = min(a.db_begin for a in r._get_alignments())
                    db_end = max(a.db_end for a in r._get_alignments())
                    lp.write(target_entity_id=e._id, db_name=r.db_name,
                             db_code=r.db_code, db_accession=r.accession,
                             seq_db_align_begin=db_begin,
                             seq_db_align_end=db_end)


class _SoftwareGroupDumper(Dumper):
    def finalize(self, system):
        seen_groups = {}
        self._group_by_id = []
        # Use _group_id rather than _id as the "group" might be a singleton
        # Software, which already has its own id
        for g in system._all_software_and_groups():
            util._remove_id(g, attr='_group_id')
        for g in system._all_software_and_groups():
            util._assign_id(g, seen_groups, self._group_by_id,
                            attr='_group_id')

    def dump(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_software_group",
                ["ordinal_id", "group_id", "software_id",
                 "parameter_group_id"]) as lp:
            for g in self._group_by_id:
                if isinstance(g, ma.Software):
                    # If a singleton Software, write a group containing one
                    # member
                    lp.write(ordinal_id=next(ordinal), group_id=g._group_id,
                             software_id=g._id)
                else:
                    for s in g:
                        lp.write(ordinal_id=next(ordinal),
                                 group_id=g._group_id, software_id=s._id)


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


class _DataGroupDumper(Dumper):
    def finalize(self, system):
        seen_groups = {}
        self._group_by_id = []
        # Use _data_group_id rather than _id as the "group" might be a
        # singleton Data, which already has its own id
        for g in system._all_data_groups():
            util._remove_id(g, attr='_data_group_id')
        for g in system._all_data_groups():
            util._assign_id(g, seen_groups, self._group_by_id,
                            attr='_data_group_id')

    def dump(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_data_group",
                ["ordinal_id", "group_id", "data_id"]) as lp:
            for g in self._group_by_id:
                if isinstance(g, ma.data.Data):
                    # If a singleton Data, write a group containing one
                    # member
                    lp.write(ordinal_id=next(ordinal),
                             group_id=g._data_group_id, data_id=g._data_id)
                else:
                    for d in g:
                        lp.write(ordinal_id=next(ordinal),
                                 group_id=g._data_group_id, data_id=d._data_id)


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


class _AlignmentDumper(Dumper):
    def finalize(self, system):
        for n, tmpl in enumerate(system.templates):
            tmpl._id = n + 1
        for n, segment in enumerate(system.template_segments):
            # Cannot use _id since segment might also be a complete template
            # (with _id = template id)
            segment._segment_id = n + 1
        for n, aln in enumerate(system.alignments):
            aln._id = n + 1

    def dump(self, system, writer):
        self.dump_template_details(system, writer)
        self.dump_template_poly(system, writer)
        self.dump_template_poly_segment(system, writer)
        self.dump_target_template_poly_mapping(system, writer)
        self.dump_info(system, writer)
        self.dump_details(system, writer)
        self.dump_sequences(system, writer)

    def dump_template_details(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_template_details",
                ["ordinal_id", "template_id", "template_origin",
                 "template_entity_type", "template_trans_matrix_id",
                 "template_data_id", "target_asym_id",
                 "template_label_asym_id",
                 "template_label_entity_id", "template_model_num"]) as lp:
            for a in system.alignments:
                for s in a.pairs:
                    # get Template from TemplateSegment
                    tmpl = s.template.template
                    lp.write(ordinal_id=next(ordinal),
                             template_id=tmpl._id,
                             template_data_id=tmpl._data_id,
                             target_asym_id=s.target.asym._id,
                             template_label_asym_id=tmpl.asym_id,
                             template_label_entity_id=tmpl.entity._id,
                             template_model_num=tmpl.model_num)

    def _get_sequence(self, entity):
        """Get the sequence for an entity as a string"""
        # Split into lines to get tidier CIF output
        return "\n".join(_prettyprint_seq((comp.code if len(comp.code) == 1
                                           else '(%s)' % comp.code
                                           for comp in entity.sequence), 70))

    def _get_canon(self, entity):
        """Get the canonical sequence for an entity as a string"""
        # Split into lines to get tidier CIF output
        seq = "\n".join(_prettyprint_seq(
            (comp.code_canonical for comp in entity.sequence), 70))
        return seq

    def dump_template_poly(self, system, writer):
        with writer.loop(
                "_ma_template_poly",
                ["template_id", "seq_one_letter_code",
                 "seq_one_letter_code_can"]) as lp:
            for tmpl in system.templates:
                entity = tmpl.entity
                lp.write(template_id=tmpl._id,
                         seq_one_letter_code=self._get_sequence(entity),
                         seq_one_letter_code_can=self._get_canon(entity))

    def dump_template_poly_segment(self, system, writer):
        with writer.loop("_ma_template_poly_segment",
                         ["id", "template_id", "residue_number_begin",
                          "residue_number_end"]) as lp:
            for s in system.template_segments:
                lp.write(
                    id=s._segment_id, template_id=s.template._id,
                    residue_number_begin=s.seq_id_range[0],
                    residue_number_end=s.seq_id_range[1])

    def dump_target_template_poly_mapping(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop("_ma_target_template_poly_mapping",
                         ["id", "template_segment_id", "target_asym_id",
                          "target_seq_id_begin", "target_seq_id_end"]) as lp:
            for a in system.alignments:
                for p in a.pairs:
                    lp.write(
                        id=next(ordinal),
                        template_segment_id=p.template._segment_id,
                        target_asym_id=p.target.asym._id,
                        target_seq_id_begin=p.target.seq_id_range[0],
                        target_seq_id_end=p.target.seq_id_range[1])

    def dump_info(self, system, writer):
        with writer.loop(
                "_ma_alignment_info",
                ["alignment_id", "data_id", "software_group_id",
                 "alignment_length", "alignment_type",
                 "alignment_mode"]) as lp:
            for a in system.alignments:
                lp.write(alignment_id=a._id, data_id=a._data_id,
                         software_group_id=a.software._group_id if a.software
                         else None,
                         alignment_type=a.type, alignment_mode=a.mode,
                         alignment_type_other_details=a.other_details)

    def dump_details(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_alignment_details",
                ["ordinal_id", "alignment_id", "template_segment_id",
                 "target_asym_id", "score_type",
                 "score_type_other_details", "score_value",
                 "percent_sequence_identity",
                 "sequence_identity_denominator"]) as lp:
            for a in system.alignments:
                for s in a.pairs:
                    lp.write(ordinal_id=next(ordinal), alignment_id=a._id,
                             template_segment_id=s.template._segment_id,
                             target_asym_id=s.target.asym._id,
                             score_type=s.score.type,
                             score_type_other_details=s.score.other_details,
                             score_value=s.score.value)

    def dump_sequences(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_alignment",
                ["ordinal_id", "alignment_id", "target_template_flag",
                 "sequence"]) as lp:
            for a in system.alignments:
                # todo: don't duplicate sequences
                for s in a.pairs:
                    # 1=target, 2=template
                    lp.write(ordinal_id=next(ordinal), alignment_id=a._id,
                             target_template_flag=1,
                             sequence=s.target.gapped_sequence)
                    lp.write(ordinal_id=next(ordinal), alignment_id=a._id,
                             target_template_flag=2,
                             sequence=s.template.gapped_sequence)


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
                             software_group_id=s.software._group_id
                             if s.software else None,
                             input_data_group_id=s.input_data._data_group_id,
                             output_data_group_id=s.output_data._data_group_id)


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


class _QAMetricDumper(Dumper):
    def finalize(self, system):
        # Get all metric classes used by all systems
        seen_metric_classes = set()
        self._metric_classes_by_id = []
        metric_id = itertools.count(1)
        for group, model in system._all_models():
            for m in model.qa_metrics:
                cls = type(m)
                if cls not in seen_metric_classes:
                    seen_metric_classes.add(cls)
                    cls._id = next(metric_id)
                    self._metric_classes_by_id.append(cls)

    def dump(self, system, writer):
        self.dump_metric_types(system, writer)
        self.dump_metric_global(system, writer)

    def dump_metric_types(self, system, writer):
        with writer.loop(
                "_ma_qa_metric",
                ["id", "name", "description", "type", "mode",
                 "type_other_details", "software_group_id"]) as lp:
            for m in self._metric_classes_by_id:
                lp.write(id=m._id, name=m.name, description=m.description,
                         type=m.type, mode=m.mode,
                         type_other_details=m.other_details,
                         software_group_id=m.software._group_id if m.software
                         else None)

    def dump_metric_global(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_qa_metric_global",
                ["ordinal_id", "model_id", "metric_id", "metric_value"]) as lp:
            for group, model in system._all_models():
                for m in model.qa_metrics:
                    if not isinstance(m, ma.qa_metric.Global):
                        pass
                    lp.write(ordinal_id=next(ordinal), model_id=model._id,
                             metric_id=m._id, metric_value=m.value)


class ModelArchiveVariant(Variant):
    _dumpers = [
        ihm.dumper._EntryDumper,  # must be first
        ihm.dumper._StructDumper, ihm.dumper._CommentDumper,
        _AuditConformDumper, ihm.dumper._CitationDumper,
        ihm.dumper._SoftwareDumper, _SoftwareGroupDumper,
        ihm.dumper._AuditAuthorDumper,
        ihm.dumper._GrantDumper, ihm.dumper._ChemCompDumper,
        ihm.dumper._EntityDumper,
        ihm.dumper._EntitySrcGenDumper, ihm.dumper._EntitySrcNatDumper,
        ihm.dumper._EntitySrcSynDumper, _TargetRefDBDumper,
        ihm.dumper._EntityPolyDumper, ihm.dumper._EntityNonPolyDumper,
        ihm.dumper._EntityPolySeqDumper, ihm.dumper._StructAsymDumper,
        ihm.dumper._PolySeqSchemeDumper, ihm.dumper._NonPolySchemeDumper,
        _DataDumper, _DataGroupDumper, _AssemblyDumper, _AlignmentDumper,
        _ProtocolDumper, _ModelDumper, _QAMetricDumper]

    def get_dumpers(self):
        return [d() for d in self._dumpers]


def write(fh, systems, format='mmCIF', dumpers=[], variant=ModelArchiveVariant):
    return ihm.dumper.write(fh, systems, format, dumpers, variant)
