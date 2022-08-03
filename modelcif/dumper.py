"""Utility classes to dump out information in mmCIF or BinaryCIF format"""

from datetime import date
import itertools
import operator
import ihm.dumper
import ihm
import ihm.format
import ihm.format_bcif
from ihm.dumper import Dumper, Variant, _prettyprint_seq, _get_transform
import modelcif.qa_metric
import modelcif.data


class _AuditConformDumper(Dumper):
    URL = ("https://raw.githubusercontent.com/ihmwg/ModelCIF/%s/base/" +
           "mmcif_ma-core.dic")

    def dump(self, system, writer):
        with writer.category("_audit_conform") as lp:
            # Update to match the version of the ModelCIF dictionary
            # we support:
            lp.write(dict_name="mmcif_ma.dic", dict_version="1.4.1",
                     dict_location=self.URL % "557bda7")


class _EntryLinkDumper(Dumper):
    def dump(self, system, writer):
        with writer.loop("_entry_link", ["id", "entry_id", "details"]) as lp:
            lp.write(id=1, entry_id=system.id, details=system.entry_details)


class _ExptlDumper(Dumper):
    def dump(self, system, writer):
        with writer.category("_exptl") as lp:
            lp.write(entry_id=system.id, method='THEORETICAL MODEL')


class _DatabaseDumper(Dumper):
    def dump(self, system, writer):
        if system.database:
            with writer.category("_database_2") as lp:
                lp.write(database_id=system.database.id,
                         database_code=system.database.code)


class _ChemCompDumper(Dumper):
    # Similar to ihm.dumper._ChemCompDumper, but we need to also include
    # components referenced only by Templates, as their Entities are not
    # included in system.entities by default

    _prov_map = {'core': 'CCD Core', 'ma': 'CCD MA', 'local': 'CCD local'}

    def _get_entities(self, system):
        return itertools.chain(
            system.entities, (t.entity for t in system.templates))

    def _get_provenance(self, comp):
        # Older python-ihm does not provide ChemComp.ccd
        ccd = comp.ccd if hasattr(comp, 'ccd') else None
        if ccd is None:
            ccd = 'core'
            if hasattr(comp, 'descriptors') and comp.descriptors:
                ccd = 'local'
        val = self._prov_map.get(ccd)
        if not val:
            raise KeyError("Invalid ccd value %s for %s; can be %s, or None"
                           % (repr(comp.ccd), comp,
                              ", ".join(sorted(self._prov_map.keys()))))
        return val

    def dump(self, system, writer):
        comps = frozenset(
            comp for e in self._get_entities(system) for comp in e.sequence)

        with writer.loop("_chem_comp", ["id", "type", "name",
                                        "formula", "formula_weight",
                                        "ma_provenance"]) as lp:
            for comp in sorted(comps, key=operator.attrgetter('id')):
                lp.write(id=comp.id, type=comp.type, name=comp.name,
                         formula=comp.formula,
                         formula_weight=comp.formula_weight,
                         ma_provenance=self._get_provenance(comp))


class _ChemCompDescriptorDumper(Dumper):
    def _get_entities(self, system):
        return itertools.chain(
            system.entities, (t.entity for t in system.templates))

    def dump(self, system, writer):
        ordinal = itertools.count(1)
        comps = frozenset(
            comp for e in self._get_entities(system) for comp in e.sequence)

        with writer.loop("_ma_chem_comp_descriptor",
                         ["ordinal_id", "chem_comp_id", "chem_comp_name",
                          "type", "value", "details", "software_id"]) as lp:
            for comp in sorted(comps, key=operator.attrgetter('id')):
                if not hasattr(comp, 'descriptors') or not comp.descriptors:
                    continue
                for desc in comp.descriptors:
                    lp.write(ordinal_id=next(ordinal), chem_comp_id=comp.id,
                             chem_comp_name=comp.name, type=desc.type,
                             value=desc.value, details=desc.details,
                             software_id=desc.software._id
                             if desc.software else None)


class _TargetRefDBDumper(Dumper):
    def dump(self, system, writer):
        # Since target_entities is a *subset* of all entities, they may not
        # be ordered by ID. Sort them so the output is prettier.
        entities = sorted(system.target_entities,
                          key=operator.attrgetter('_id'))
        with writer.loop(
                "_ma_target_ref_db_details",
                ["target_entity_id", "db_name", "db_name_other_details",
                 "db_code", "db_accession", "seq_db_isoform",
                 "seq_db_align_begin", "seq_db_align_end",
                 "ncbi_taxonomy_id", "organism_scientific",
                 "seq_db_sequence_version_date",
                 "seq_db_sequence_checksum"]) as lp:
            for e in entities:
                for r in e.references:
                    db_begin = (e.seq_id_range[0] if r.align_begin is None
                                else r.align_begin)
                    db_end = (e.seq_id_range[1] if r.align_end is None
                              else r.align_end)
                    lp.write(target_entity_id=e._id, db_name=r.name,
                             db_name_other_details=r.other_details,
                             db_code=r.code, db_accession=r.accession,
                             seq_db_isoform=r.isoform,
                             seq_db_align_begin=db_begin,
                             seq_db_align_end=db_end,
                             ncbi_taxonomy_id=r.ncbi_taxonomy_id,
                             organism_scientific=r.organism_scientific,
                             seq_db_sequence_version_date=date.isoformat(
                                 r.sequence_version_date)
                             if r.sequence_version_date else None,
                             seq_db_sequence_checksum=r.sequence_crc64)


class _EntityNonPolyDumper(Dumper):
    def finalize(self, system):
        self._ma_model_mode_map = {}
        expmap = {True: 'explicit', False: 'implicit'}
        for a in system.asym_units:
            if isinstance(a, modelcif.NonPolymerFromTemplate):
                self._ma_model_mode_map[a.template.entity] = \
                    expmap.get(a.explicit)

    def dump(self, system, writer):
        with writer.loop("_pdbx_entity_nonpoly",
                         ["entity_id", "name", "comp_id",
                          "ma_model_mode"]) as lp:
            for entity in system.entities:
                if entity.is_polymeric():
                    continue
                lp.write(entity_id=entity._id, name=entity.description,
                         comp_id=entity.sequence[0].id,
                         ma_model_mode=self._ma_model_mode_map.get(entity))


class _TargetEntityDumper(Dumper):
    def dump(self, system, writer):
        entities = sorted(system.target_entities,
                          key=operator.attrgetter('_id'))
        with writer.loop(
                "_ma_target_entity",
                ["entity_id", "data_id", "origin"]) as lp:
            for e in entities:
                lp.write(entity_id=e._id, data_id=e._data_id,
                         origin="reference database" if e.references
                         else "designed")

        with writer.loop(
                "_ma_target_entity_instance",
                ["asym_id", "entity_id", "details"]) as lp:
            for asym in system.asym_units:
                lp.write(asym_id=asym._id, entity_id=asym.entity._id,
                         details=asym.details)


class _SoftwareGroupDumper(Dumper):
    def finalize(self, system):
        # Map from id(list) to id
        self._param_group_id = {}
        self._param_groups = []
        for n, s in enumerate(system.software_groups):
            # Use _group_id rather than _id as the "group" might be a
            # singleton Software, which already has its own id
            s._group_id = n + 1
            if (isinstance(s, modelcif.SoftwareGroup) and s.parameters
                    and id(s.parameters) not in self._param_groups):
                self._param_groups.append(s.parameters)
                self._param_group_id[id(s.parameters)] \
                    = len(self._param_groups)

    def dump(self, system, writer):
        self.dump_parameters(system, writer)
        self.dump_groups(system, writer)

    def dump_groups(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_software_group",
                ["ordinal_id", "group_id", "software_id",
                 "parameter_group_id"]) as lp:
            for g in system.software_groups:
                if isinstance(g, modelcif.Software):
                    # If a singleton Software, write a group containing one
                    # member
                    lp.write(ordinal_id=next(ordinal), group_id=g._group_id,
                             software_id=g._id)
                else:
                    param = None
                    if g.parameters:
                        param = self._param_group_id[id(g.parameters)]
                    for s in g:
                        lp.write(ordinal_id=next(ordinal),
                                 group_id=g._group_id, software_id=s._id,
                                 parameter_group_id=param)

    def _handle_list(self, value):
        list_type_map = {int: 'integer-csv', float: 'float-csv'}
        types = frozenset(type(x) for x in value)
        if types == frozenset((int,)):
            data_type = list_type_map[int]
        elif types == frozenset((float,)) or types == frozenset((int, float)):
            # Treat mix of int and float as float
            data_type = list_type_map[float]
        else:
            raise TypeError("Only lists of ints or floats are supported")
        return data_type, ",".join(str(x) for x in value)

    def dump_parameters(self, system, writer):
        parameter_id = itertools.count(1)
        type_map = {int: "integer", float: "float", str: "string",
                    bool: "boolean"}
        with writer.loop(
                "_ma_software_parameter",
                ["parameter_id", "group_id", "data_type",
                 "name", "value", "description"]) as lp:
            for g in self._param_groups:
                group_id = self._param_group_id[id(g)]
                for p in g:
                    if isinstance(p.value, (list, tuple)):
                        data_type, value = self._handle_list(p.value)
                    else:
                        data_type = type_map.get(type(p.value), str)
                        value = p.value
                    lp.write(parameter_id=next(parameter_id),
                             group_id=group_id, data_type=data_type,
                             name=p.name, value=value,
                             description=p.description)


class _DataDumper(Dumper):
    def finalize(self, system):
        for n, d in enumerate(system.data):
            d._data_id = n + 1

    def dump(self, system, writer):
        with writer.loop(
                "_ma_data",
                ["id", "name", "content_type",
                 "content_type_other_details"]) as lp:
            for d in system.data:
                # ihm.Entity isn't a subclass of Data, so we need
                # to fill in missing attributes here
                if isinstance(d, ihm.Entity):
                    lp.write(id=d._data_id, name=d.description,
                             content_type="target",
                             content_type_other_details=None)
                else:
                    lp.write(id=d._data_id, name=d.name,
                             content_type=d.data_content_type,
                             content_type_other_details=d.data_other_details)


class _DataGroupDumper(Dumper):
    def finalize(self, system):
        for n, d in enumerate(system.data_groups):
            # Use _data_group_id rather than _id as the "group" might be a
            # singleton Data, which already has its own id
            d._data_group_id = n + 1

    def dump(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_data_group",
                ["ordinal_id", "group_id", "data_id"]) as lp:
            for g in system.data_groups:
                if isinstance(g, (modelcif.data.Data, ihm.Entity)):
                    # If a singleton Data (or ihm.Entity, which isn't a
                    # subclass of Data), write a group containing one member
                    lp.write(ordinal_id=next(ordinal),
                             group_id=g._data_group_id, data_id=g._data_id)
                else:
                    for d in g:
                        lp.write(ordinal_id=next(ordinal),
                                 group_id=g._data_group_id, data_id=d._data_id)


class _DataRefDBDumper(Dumper):
    def dump(self, system, writer):
        with writer.loop(
                "_ma_data_ref_db",
                ["data_id", "name", "location_url",
                 "version", "release_date"]) as lp:
            for d in system.data:
                if not isinstance(d, modelcif.ReferenceDatabase):
                    continue
                lp.write(data_id=d._data_id, name=d.name, location_url=d.url,
                         version=d.version,
                         release_date=date.isoformat(d.release_date)
                         if d.release_date else None)


class _TemplateTransformDumper(Dumper):
    def finalize(self, system):
        for n, trans in enumerate(system.template_transformations):
            trans._id = n + 1

    def dump(self, system, writer):
        with writer.loop(
                "_ma_template_trans_matrix",
                ["id",
                 "rot_matrix[1][1]", "rot_matrix[2][1]", "rot_matrix[3][1]",
                 "rot_matrix[1][2]", "rot_matrix[2][2]", "rot_matrix[3][2]",
                 "rot_matrix[1][3]", "rot_matrix[2][3]", "rot_matrix[3][3]",
                 "tr_vector[1]", "tr_vector[2]", "tr_vector[3]"]) as lp:
            for t in system.template_transformations:
                lp.write(id=t._id,
                         **_get_transform(t.rot_matrix, t.tr_vector))


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
        self.dump_template_non_poly(system, writer)
        self.dump_template_ref_db(system, writer)
        self.dump_target_template_poly_mapping(system, writer)
        self.dump_info(system, writer)
        self.dump_details(system, writer)
        self.dump_sequences(system, writer)

    def dump_template_details(self, system, writer):
        ordinal = itertools.count(1)

        def write_template(tmpl, tgt_asym, lp):
            org = ("reference database" if tmpl.references
                   else "customized")
            poly = ("polymer" if tmpl.entity.is_polymeric()
                    else "non-polymer")
            lp.write(ordinal_id=next(ordinal),
                     template_id=tmpl._id,
                     template_origin=org,
                     template_entity_type=poly,
                     template_trans_matrix_id=tmpl.transformation._id,
                     template_data_id=tmpl._data_id,
                     target_asym_id=tgt_asym._id if tgt_asym else None,
                     template_label_asym_id=tmpl.asym_id,
                     template_label_entity_id=tmpl.entity_id,
                     template_model_num=tmpl.model_num,
                     template_auth_asym_id=tmpl.strand_id)

        with writer.loop(
                "_ma_template_details",
                ["ordinal_id", "template_id", "template_origin",
                 "template_entity_type", "template_trans_matrix_id",
                 "template_data_id", "target_asym_id",
                 "template_label_asym_id",
                 "template_label_entity_id", "template_model_num",
                 "template_auth_asym_id"]) as lp:
            seen_templates = set()
            for a in system.alignments:
                for s in a.pairs:
                    # get Template from TemplateSegment
                    write_template(s.template.template, s.target.asym, lp)
                    seen_templates.add(s.template.template)
            # Handle all non-polymer templates (not in alignments)
            for a in system.asym_units:
                if isinstance(a, modelcif.NonPolymerFromTemplate):
                    write_template(a.template, a, lp)
                    seen_templates.add(a.template)
            # Handle all remaining non-aligned templates
            for t in system.templates:
                if t not in seen_templates:
                    write_template(t, None, lp)

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
                if not entity.is_polymeric():
                    continue
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

    def dump_template_non_poly(self, system, writer):
        with writer.loop(
                "_ma_template_non_poly",
                ["template_id", "comp_id", "details"]) as lp:
            for tmpl in system.templates:
                entity = tmpl.entity
                if entity.is_polymeric():
                    continue
                lp.write(template_id=tmpl._id, comp_id=entity.sequence[0].id,
                         details=entity.description)

    def dump_template_ref_db(self, system, writer):
        with writer.loop(
                "_ma_template_ref_db_details",
                ["template_id", "db_name", "db_name_other_details",
                 "db_accession_code"]) as lp:
            for tmpl in system.templates:
                for ref in tmpl.references:
                    lp.write(template_id=tmpl._id, db_name=ref.name,
                             db_name_other_details=ref.other_details,
                             db_accession_code=ref.accession)

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
                if a.pairs:
                    align_len = max(len(s.gapped_sequence) for pair in a.pairs
                                    for s in (pair.template, pair.target))
                else:
                    align_len = None
                lp.write(alignment_id=a._id, data_id=a._data_id,
                         software_group_id=a.software._group_id if a.software
                         else None,
                         alignment_type=a.type, alignment_mode=a.mode,
                         alignment_length=align_len,
                         alignment_type_other_details=a.other_details)

    def dump_details(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_alignment_details",
                ["ordinal_id", "alignment_id", "template_segment_id",
                 "target_asym_id", "score_type",
                 "score_type_other_details", "score_value",
                 "percent_sequence_identity",
                 "sequence_identity_denominator",
                 "sequence_identity_denominator_other_details"]) as lp:
            for a in system.alignments:
                for s in a.pairs:
                    denom = s.identity.denominator
                    od = s.identity.other_details
                    lp.write(ordinal_id=next(ordinal), alignment_id=a._id,
                             template_segment_id=s.template._segment_id,
                             target_asym_id=s.target.asym._id,
                             score_type=s.score.type,
                             score_type_other_details=s.score.other_details,
                             score_value=s.score.value,
                             percent_sequence_identity=s.identity.value,
                             sequence_identity_denominator=denom,
                             sequence_identity_denominator_other_details=od)

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
                          "model_name", "model_group_name",
                          "data_id", "model_type",
                          "model_type_other_details"]) as lp:
            for group in system.model_groups:
                for model in group:
                    lp.write(ordinal_id=next(ordinal), model_id=model._id,
                             model_group_id=group._id, model_name=model.name,
                             model_group_name=group.name,
                             data_id=model._data_id,
                             model_type=model.model_type,
                             model_type_other_details=model.other_details)


class _AssociatedDumper(Dumper):
    def finalize(self, system):
        file_id = itertools.count(1)
        in_archive_file_id = itertools.count(1)
        for repo in system.repositories:
            for f in repo.files:
                f._id = next(file_id)
                if hasattr(f, 'files'):
                    for af in f.files:
                        if hasattr(af, 'files'):
                            raise ValueError(
                                "An archive cannot contain another archive")
                        af._id = next(in_archive_file_id)

    def dump(self, system, writer):
        self.dump_files(system, writer)
        self.dump_archive_files(system, writer)

    def dump_files(self, system, writer):
        with writer.loop(
                "_ma_entry_associated_files",
                ["id", "entry_id", "file_url", "file_type", "file_format",
                 "file_content", "details"]) as lp:
            for repo in system.repositories:
                for f in repo.files:
                    lp.write(id=f._id, entry_id=system.id,
                             file_url=repo.get_url(f), file_type=f.file_type,
                             file_format=f.file_format,
                             file_content=f.file_content, details=f.details)

    def dump_archive_files(self, system, writer):
        with writer.loop(
                "_ma_associated_archive_file_details",
                ["id", "archive_file_id", "file_path", "file_format",
                 "file_content", "description"]) as lp:
            for repo in system.repositories:
                for f in repo.files:
                    if not hasattr(f, 'files'):
                        continue
                    for af in f.files:
                        lp.write(id=af._id, archive_file_id=f._id,
                                 file_path=af.path, file_format=af.file_format,
                                 file_content=af.file_content,
                                 description=af.details)


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
                    # We need an instance of the class in case name or
                    # description are provided by property()
                    self._metric_classes_by_id.append(m)

    def dump(self, system, writer):
        self.dump_metric_types(system, writer)
        self.dump_metric_global(system, writer)
        self.dump_metric_local(system, writer)
        self.dump_metric_pairwise(system, writer)

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
                    if not isinstance(m, modelcif.qa_metric.Global):
                        continue
                    lp.write(ordinal_id=next(ordinal), model_id=model._id,
                             metric_id=m._id, metric_value=m.value)

    def dump_metric_local(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_qa_metric_local",
                ["ordinal_id", "model_id", "label_asym_id", "label_seq_id",
                 "label_comp_id", "metric_id", "metric_value"]) as lp:
            for group, model in system._all_models():
                for m in model.qa_metrics:
                    if not isinstance(m, modelcif.qa_metric.Local):
                        continue
                    seq = m.residue.asym.entity.sequence
                    lp.write(ordinal_id=next(ordinal), model_id=model._id,
                             label_asym_id=m.residue.asym._id,
                             label_seq_id=m.residue.seq_id,
                             label_comp_id=seq[m.residue.seq_id - 1].id,
                             metric_id=m._id, metric_value=m.value)

    def dump_metric_pairwise(self, system, writer):
        ordinal = itertools.count(1)
        with writer.loop(
                "_ma_qa_metric_local_pairwise",
                ["ordinal_id", "model_id", "label_asym_id_1", "label_seq_id_1",
                 "label_comp_id_1", "label_asym_id_2", "label_seq_id_2",
                 "label_comp_id_2", "metric_id", "metric_value"]) as lp:
            for group, model in system._all_models():
                for m in model.qa_metrics:
                    if not isinstance(m, modelcif.qa_metric.LocalPairwise):
                        continue
                    seq1 = m.residue1.asym.entity.sequence
                    seq2 = m.residue2.asym.entity.sequence
                    lp.write(ordinal_id=next(ordinal), model_id=model._id,
                             label_asym_id_1=m.residue1.asym._id,
                             label_seq_id_1=m.residue1.seq_id,
                             label_comp_id_1=seq1[m.residue1.seq_id - 1].id,
                             label_asym_id_2=m.residue2.asym._id,
                             label_seq_id_2=m.residue2.seq_id,
                             label_comp_id_2=seq2[m.residue2.seq_id - 1].id,
                             metric_id=m._id, metric_value=m.value)


class _CopyWriter(object):
    """Context manager to write loop or category to two mmCIF/BinaryCIF
       files"""
    def __init__(self, w1, w2):
        self.w1, self.w2 = w1, w2

    def write(self, *args, **keys):
        self.w1.write(*args, **keys)
        self.w2.write(*args, **keys)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # This may not correctly handle exceptions raised within the loop
        self.w1.__exit__(exc_type, exc_value, traceback)
        self.w2.__exit__(exc_type, exc_value, traceback)


class _SystemWriter(object):
    """Utility class which normally just passes through to the default
       ``base_writer``, but outputs selected categories to associated files."""
    def __init__(self, base_writer, category_map, copy_category_map):
        self._base_writer = base_writer
        self.category_map = category_map
        self.copy_category_map = copy_category_map

    def category(self, category):
        w = self.copy_category_map.get(category)
        if w:
            return _CopyWriter(w.category(category),
                               self._base_writer.category(category))
        else:
            w = self.category_map.get(category, self._base_writer)
            return w.category(category)

    def loop(self, category, keys):
        w = self.copy_category_map.get(category)
        if w:
            return _CopyWriter(w.loop(category, keys),
                               self._base_writer.loop(category, keys))
        else:
            w = self.category_map.get(category, self._base_writer)
            return w.loop(category, keys)

    def end_block(self):
        # Flush and close all file handles of associated files
        for w in self.category_map.values():
            if not hasattr(w, 'fh'):
                continue
            w.flush()
            w.fh.close()
            del w.fh

    # Just pass through to base writer object
    def flush(self):
        return self._base_writer.flush()

    def start_block(self, name):
        return self._base_writer.start_block(name)

    def write_comment(self, comment):
        return self._base_writer.write_comment(comment)


class ModelCIFVariant(Variant):
    """Used to select typical PDBx/ModelCIF file output.
       See :func:`write` and :class:`ihm.dumper.Variant`."""
    _dumpers = [
        ihm.dumper._EntryDumper,  # must be first
        ihm.dumper._StructDumper, _ExptlDumper, ihm.dumper._CommentDumper,
        _AuditConformDumper, _DatabaseDumper, ihm.dumper._CitationDumper,
        ihm.dumper._SoftwareDumper, _SoftwareGroupDumper,
        ihm.dumper._AuditAuthorDumper,
        ihm.dumper._GrantDumper, _ChemCompDumper, _ChemCompDescriptorDumper,
        ihm.dumper._EntityDumper,
        ihm.dumper._EntitySrcGenDumper, ihm.dumper._EntitySrcNatDumper,
        ihm.dumper._EntitySrcSynDumper, _TargetRefDBDumper,
        ihm.dumper._EntityPolyDumper, _EntityNonPolyDumper,
        ihm.dumper._EntityPolySeqDumper, ihm.dumper._StructAsymDumper,
        ihm.dumper._PolySeqSchemeDumper, ihm.dumper._NonPolySchemeDumper,
        _DataDumper, _DataGroupDumper, _DataRefDBDumper,
        _TargetEntityDumper, _TemplateTransformDumper, _AlignmentDumper,
        _ProtocolDumper, _ModelDumper, _AssociatedDumper, _QAMetricDumper]

    def get_dumpers(self):
        return [d() for d in self._dumpers]

    def get_system_writer(self, system, writer_class, writer):
        # Get a Writer-like object which outputs selected categories to
        # associated files (the rest use the default writer)
        category_map = {}
        copy_category_map = {}

        def _all_repo_files(r):
            for f in r.files:
                yield f
                if hasattr(f, 'files'):
                    for subf in f.files:
                        yield subf
        for r in system.repositories:
            for f in _all_repo_files(r):
                if (not hasattr(f, 'categories')
                        or (not f.categories and not f.copy_categories)):
                    continue
                if f.binary:
                    w = ihm.format_bcif.BinaryCifWriter(
                        open(f.local_path, 'wb'))
                else:
                    w = ihm.format.CifWriter(open(f.local_path, 'w'))
                # Write header information to the associated file
                dumpers = (ihm.dumper._EntryDumper(), _EntryLinkDumper())
                # We are passing the File object to the dumpers here where
                # they expect a System object, but the interfaces are similar
                # enough, so we don't need a facade object.
                for d in dumpers:
                    d.finalize(f)
                for d in dumpers:
                    d.dump(f, w)
                for c in f.categories:
                    # Allow for categories with or without leading underscore
                    category_map['_' + c.lstrip('_').lower()] = w
                for c in f.copy_categories:
                    copy_category_map['_' + c.lstrip('_').lower()] = w
        if category_map or copy_category_map:
            return _SystemWriter(writer, category_map, copy_category_map)
        else:
            # If no categories, we can just use the base writer
            return writer


def write(fh, systems, format='mmCIF', dumpers=[],
          variant=ModelCIFVariant):
    """Write out all `systems` to the file handle `fh`.

       See :func:`ihm.dumper.write` for more information. The function
       here behaves similarly but writes out files compliant with the
       ModelCIF extension directory rather than IHM."""
    return ihm.dumper.write(fh, systems, format, dumpers, variant)
