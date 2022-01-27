"""Utility classes to read in information in mmCIF or BinaryCIF format"""

import modelcif
import modelcif.model
import modelcif.protocol
import modelcif.qa_metric
import modelcif.alignment
import modelcif.reference
import ihm
import ihm.source
import ihm.reader
from ihm.reader import Variant, Handler, IDMapper, _ChemCompIDMapper
from ihm.reader import OldFileError, _make_new_entity
import operator
import inspect
import collections


class _AuditConformHandler(Handler):
    category = '_audit_conform'

    def __call__(self, dict_name, dict_version):
        # Reject old file versions if we can parse the version
        if dict_name == "mmcif_ma.dic":
            try:
                major, minor, _ = [int(x) for x in dict_version.split('.')]
                if (major, minor) < (1, 3):
                    raise OldFileError(
                        "This version of python-modelcif only supports "
                        "reading files that conform to version 1.3 or later "
                        "of the ModelCIF extension dictionary. This file "
                        "conforms to version %s." % dict_version)
            except ValueError:
                pass


class _SystemReader(object):
    def __init__(self, model_class, starting_model_class):
        self.system = modelcif.System()

        #: Mapping from ID to :class:`ihm.Software` objects
        self.software = IDMapper(self.system.software, ihm.Software,
                                 *(None,) * 4)

        #: Mapping from ID to :class:`ihm.Citation` objects
        self.citations = IDMapper(self.system.citations, ihm.Citation,
                                  *(None,) * 8)

        #: Mapping from ID to :class:`ihm.Entity` objects
        self.entities = IDMapper(self.system.entities, _make_new_entity)

        #: Mapping from ID to :class:`ihm.source.Manipulated` objects
        self.src_gens = IDMapper(None, ihm.source.Manipulated)

        #: Mapping from ID to :class:`ihm.source.Natural` objects
        self.src_nats = IDMapper(None, ihm.source.Natural)

        #: Mapping from ID to :class:`ihm.source.Synthetic` objects
        self.src_syns = IDMapper(None, ihm.source.Synthetic)

        #: Mapping from ID to :class:`ihm.AsymUnit` objects
        self.asym_units = IDMapper(self.system.asym_units, ihm.AsymUnit, None)

        #: Mapping from ID to :class:`ihm.ChemComp` objects
        self.chem_comps = _ChemCompIDMapper(None, ihm.ChemComp, *(None,) * 3)

        self.software_groups = IDMapper(self.system.software_groups,
                                        modelcif.SoftwareGroup)

        self.default_data_by_id = {}
        self.data_by_id = {}
        self.data_groups = IDMapper(self.system.data_groups,
                                    modelcif.data.DataGroup)

        self.transformations = IDMapper(self.system.template_transformations,
                                        modelcif.Transformation, *(None,) * 2)

        self.templates = IDMapper(self.system.templates, modelcif.Template,
                                  *(None,) * 4)

        self.template_segments = IDMapper(
            self.system.template_segments, modelcif.TemplateSegment,
            *(None,) * 4)

        self.default_model_class = model_class is modelcif.model.Model
        self._all_seen_models = []
        self.models = IDMapper(self._all_seen_models, model_class, [], None)

        self.model_groups = IDMapper(self.system.model_groups,
                                     modelcif.model.ModelGroup)

        self.assemblies = IDMapper(self.system.assemblies, modelcif.Assembly)

        self.protocols = IDMapper(self.system.protocols,
                                  modelcif.protocol.Protocol)

        self.qa_by_id = {}

        self.software_parameters = collections.defaultdict(list)

        self.alignment_pairs = collections.defaultdict(list)

        self.alignment_seqs = collections.defaultdict(list)

        self.target_template_mapping = {}

    def finalize(self):
        # make sequence immutable (see also _make_new_entity)
        for e in self.system.entities:
            e.sequence = tuple(e.sequence)


class _DatabaseHandler(Handler):
    category = '_database_2'

    def __call__(self, database_code, database_id):
        self.system.database = modelcif.Database(
            id=database_id, code=database_code)


class _SoftwareGroupHandler(Handler):
    category = '_ma_software_group'

    def __call__(self, group_id, software_id, parameter_group_id):
        g = self.sysr.software_groups.get_by_id(group_id)
        s = self.sysr.software.get_by_id(software_id)
        # Don't need to handle None or ihm.unknown specially here; this will
        # map them to an empty list
        g.parameters = self.sysr.software_parameters[parameter_group_id]
        g.append(s)


class _SoftwareParameterHandler(Handler):
    category = '_ma_software_parameter'

    def __call__(self, group_id, data_type, name, value, description):
        type_map = {"integer": self.get_int, "float": self.get_float,
                    "boolean": self.get_bool, "string": str}
        pg = self.sysr.software_parameters[group_id]
        converter = type_map.get(data_type, str)
        p = modelcif.SoftwareParameter(name=name, value=converter(value),
                                       description=description)
        pg.append(p)


class _DataHandler(Handler):
    category = '_ma_data'

    def __call__(self, id, name, content_type_other_details):
        d = modelcif.data.Data(name=name, details=content_type_other_details)
        d._data_id = id
        self.sysr.default_data_by_id[id] = d

    def finalize(self):
        for data_id, defdata in self.sysr.default_data_by_id.items():
            data = self.sysr.data_by_id.get(data_id)
            if not data:
                # Add placeholder Data if only referenced in ma_data
                self.sysr.data_by_id[data_id] = defdata
            elif hasattr(data, 'name') and not data.name:
                # Add data-specific fields if they are present in ma_data
                # but not elsewhere
                data.name = defdata.name
        self.system.data[:] = sorted(self.sysr.data_by_id.values(),
                                     key=operator.attrgetter('_data_id'))

        for g in self.system.data_groups:
            g[:] = [self.sysr.data_by_id.get(x) for x in g]


class _DataGroupHandler(Handler):
    category = '_ma_data_group'

    def __call__(self, group_id, data_id):
        g = self.sysr.data_groups.get_by_id(group_id)
        # fill in real Data objects at _DataHandler.finalize time
        g.append(data_id)


class _EnumerationMapper(object):
    """Map an mmCIF enumerated value to the corresponding Python class"""
    def __init__(self, module, base_class, attr="name"):
        self._base_class = base_class
        self._other_name = getattr(base_class, attr).upper()
        self._attr = attr
        self._map = dict(
            (getattr(x[1], attr).upper(), x[1])
            for x in inspect.getmembers(module, inspect.isclass)
            if issubclass(x[1], base_class) and x[1] is not base_class)
        self._other_map = {}

    def get(self, name, other_det):
        """Get the Python class that matches the given name
           and other_details"""
        name = name.upper()
        typ = self._map.get(name)
        if typ:
            return typ
        # If name is not Other this is an enumeration value we don't have
        # a class for; make and cache a new class for the given name:
        if name != self._other_name:
            class ExtraType(self._base_class):
                other_details = None
            setattr(ExtraType, self._attr, name)
            self._map[name] = ExtraType
            return ExtraType
        # If name is "Other" then treat other_details as the key
        other_det_up = other_det.upper()
        if other_det_up not in self._other_map:
            class CustomType(self._base_class):
                other_details = other_det
                __doc__ = other_det
            self._other_map[other_det_up] = CustomType
        return self._other_map[other_det_up]


class _TargetEntityHandler(Handler):
    category = '_ma_target_entity'

    def __call__(self, entity_id, data_id):
        e = self.sysr.entities.get_by_id(entity_id)
        self.sysr.data_by_id[data_id] = e
        e._data_id = data_id


class _TargetRefDBHandler(Handler):
    category = '_ma_target_ref_db_details'

    def __init__(self, *args):
        super(_TargetRefDBHandler, self).__init__(*args)
        # Map db_name to subclass of modelcif.reference.TargetReference
        self.type_map = _EnumerationMapper(modelcif.reference,
                                           modelcif.reference.TargetReference)

    def __call__(self, target_entity_id, db_name, db_name_other_details,
                 db_code, db_accession, seq_db_isoform, seq_db_align_begin,
                 seq_db_align_end, ncbi_taxonomy_id, organism_scientific):
        e = self.sysr.entities.get_by_id(target_entity_id)
        typ = self.type_map.get(db_name, db_name_other_details)
        ref = typ(code=db_code, accession=db_accession,
                  align_begin=self.get_int(seq_db_align_begin),
                  align_end=self.get_int(seq_db_align_end),
                  isoform=seq_db_isoform, ncbi_taxonomy_id=ncbi_taxonomy_id,
                  organism_scientific=organism_scientific)
        e.references.append(ref)


class _TransformationHandler(Handler):
    category = '_ma_template_trans_matrix'

    def __call__(self, id, tr_vector1, tr_vector2, tr_vector3, rot_matrix11,
                 rot_matrix21, rot_matrix31, rot_matrix12, rot_matrix22,
                 rot_matrix32, rot_matrix13, rot_matrix23, rot_matrix33):
        t = self.sysr.transformations.get_by_id(id)
        t.rot_matrix = ihm.reader._get_matrix33(locals(), 'rot_matrix')
        t.tr_vector = ihm.reader._get_vector3(locals(), 'tr_vector')


class _TemplateDetailsHandler(Handler):
    category = '_ma_template_details'

    def __call__(self, template_id, template_trans_matrix_id,
                 template_data_id, target_asym_id, template_label_asym_id,
                 template_label_entity_id, template_model_num):
        template = self.sysr.templates.get_by_id(template_id)
        template.transformation = self.sysr.transformations.get_by_id(
            template_trans_matrix_id)
        template.entity = self.sysr.entities.get_by_id(
            template_label_entity_id)
        template.asym_id = template_label_asym_id
        template.model_num = self.get_int(template_model_num)
        self.sysr.data_by_id[template_data_id] = template
        template._data_id = template_data_id
        # todo: fill in target_asym_id in alignment


class _TemplateRefDBHandler(Handler):
    category = '_ma_template_ref_db_details'

    def __init__(self, *args):
        super(_TemplateRefDBHandler, self).__init__(*args)
        # Map db_name to subclass of modelcif.reference.TemplateReference
        self.type_map = _EnumerationMapper(
            modelcif.reference, modelcif.reference.TemplateReference)

    def __call__(self, template_id, db_name, db_name_other_details,
                 db_accession_code):
        t = self.sysr.templates.get_by_id(template_id)
        typ = self.type_map.get(db_name, db_name_other_details)
        ref = typ(accession=db_accession_code)
        t.references.append(ref)


class _TemplatePolySegmentHandler(Handler):
    category = '_ma_template_poly_segment'

    def __call__(self, id, template_id, residue_number_begin,
                 residue_number_end):
        segment = self.sysr.template_segments.get_by_id(id)
        segment.template = self.sysr.templates.get_by_id(template_id)
        segment.seq_id_range = (int(residue_number_begin),
                                int(residue_number_end))


def _get_align_class(type_class, mode_class, align_class_map):
    """Create and return a new class to represent an alignment"""
    k = (type_class, mode_class)
    if k not in align_class_map:
        class Alignment(type_class, mode_class):
            pass
        align_class_map[k] = Alignment
    return align_class_map[k]


class _AlignmentInfoHandler(Handler):
    category = '_ma_alignment_info'

    def __init__(self, *args):
        super(_AlignmentInfoHandler, self).__init__(*args)
        # Map type to subclass of modelcif.alignment.AlignmentType
        self._type_map = dict(
            (x[1].type.upper(), x[1])
            for x in inspect.getmembers(modelcif.alignment, inspect.isclass)
            if issubclass(x[1], modelcif.alignment.AlignmentType)
            and x[1] is not modelcif.alignment.AlignmentType)
        # Map mode to subclass of modelcif.alignment.AlignmentMode
        self._mode_map = dict(
            (x[1].mode.upper(), x[1])
            for x in inspect.getmembers(modelcif.alignment, inspect.isclass)
            if issubclass(x[1], modelcif.alignment.AlignmentMode)
            and x[1] is not modelcif.alignment.AlignmentMode)
        # Cache created Alignment classes
        self._align_class_map = {}

    def __call__(self, alignment_id, data_id, software_group_id,
                 alignment_type, alignment_mode):
        type_class = self._type_map.get(
            alignment_type.upper(), modelcif.alignment.AlignmentType)
        mode_class = self._mode_map.get(
            alignment_mode.upper(), modelcif.alignment.AlignmentMode)
        software = self.sysr.software_groups.get_by_id_or_none(
            software_group_id)
        align_class = _get_align_class(type_class, mode_class,
                                       self._align_class_map)
        alignment = align_class(name=None, pairs=[], software=software)
        alignment._id = alignment_id
        self.sysr.data_by_id[data_id] = alignment
        alignment._data_id = data_id
        self.sysr.system.alignments.append(alignment)

    def finalize(self):
        for aln in self.sysr.system.alignments:
            for pair in self.sysr.alignment_pairs[aln._id]:
                k = (pair.template._id, pair.target.asym._id)
                pair.target.seq_id_range = \
                    self.sysr.target_template_mapping.get(k)
                aln.pairs.append(pair)
            # todo: handle multiple alignments, multiple templates
            for flag, sequence in self.sysr.alignment_seqs[aln._id]:
                if flag == '2':  # template
                    aln.pairs[0].template.gapped_sequence = sequence
                else:  # target
                    aln.pairs[0].target.gapped_sequence = sequence


class _AlignmentHandler(Handler):
    category = '_ma_alignment'

    def __call__(self, alignment_id, target_template_flag, sequence):
        # Remember for later; processed by AlignmentInfoHandler.finalize()
        self.sysr.alignment_seqs[alignment_id].append((target_template_flag,
                                                       sequence))


class _AlignmentDetailsHandler(Handler):
    category = '_ma_alignment_details'

    def __init__(self, *args):
        super(_AlignmentDetailsHandler, self).__init__(*args)
        # Map denom to subclass of modelcif.alignment.Identity
        self._ident_map = _EnumerationMapper(
            modelcif.alignment, modelcif.alignment.Identity,
            attr='denominator')
        # Map score_type to subclass of modelcif.alignment.Score
        self._score_map = _EnumerationMapper(
            modelcif.alignment, modelcif.alignment.Score, attr='type')

    def __call__(self, alignment_id, template_segment_id, target_asym_id,
                 score_type, score_type_other_details, score_value,
                 percent_sequence_identity, sequence_identity_denominator,
                 sequence_identity_denominator_other_details):
        score_class = self._score_map.get(score_type, score_type_other_details)
        score = score_class(self.get_float(score_value))
        ident_class = self._ident_map.get(
            sequence_identity_denominator,
            sequence_identity_denominator_other_details)
        ident = ident_class(self.get_float(percent_sequence_identity))
        template = self.sysr.template_segments.get_by_id(template_segment_id)
        asym = self.sysr.asym_units.get_by_id(target_asym_id)
        # We don't know the target segment yet (will be filled in at finalize
        # time from the ma_target_template_poly_mapping and ma_alignment
        # tables)
        tgt_seg = asym.segment(gapped_sequence=None, seq_id_begin=None,
                               seq_id_end=None)
        p = modelcif.alignment.Pair(template=template, target=tgt_seg,
                                    identity=ident, score=score)
        # Cannot add to alignment yet as it might not exist; remember for
        # now and we'll add in finalize() of AlignmentInfoHandler
        self.sysr.alignment_pairs[alignment_id].append(p)


class _TargetTemplatePolyMappingHandler(Handler):
    category = '_ma_target_template_poly_mapping'

    def __call__(self, template_segment_id, target_asym_id,
                 target_seq_id_begin, target_seq_id_end):
        k = (template_segment_id, target_asym_id)
        rng = (self.get_int(target_seq_id_begin),
               self.get_int(target_seq_id_end))
        # Remember for now and we'll add in finalize() of AlignmentInfoHandler
        self.sysr.target_template_mapping[k] = rng


class _AssemblyHandler(Handler):
    category = '_ma_struct_assembly'

    def __call__(self, assembly_id, asym_id, seq_id_begin, seq_id_end):
        a = self.sysr.assemblies.get_by_id(assembly_id)
        asym = self.sysr.asym_units.get_by_id(asym_id)
        a.append(asym(int(seq_id_begin), int(seq_id_end)))

    def finalize(self):
        # Any AsymUnitRange which covers an entire asym,
        # replace with AsymUnit object
        for a in self.system.assemblies:
            a[:] = [self._handle_component(x) for x in a]

    def _handle_component(self, comp):
        if isinstance(comp, modelcif.AsymUnitRange) \
           and comp.seq_id_range == comp.asym.seq_id_range:
            return comp.asym
        else:
            return comp


class _AssemblyDetailsHandler(Handler):
    category = '_ma_struct_assembly_details'

    def __call__(self, assembly_id, assembly_name, assembly_description):
        a = self.sysr.assemblies.get_by_id(assembly_id)
        a.name = assembly_name
        a.description = assembly_description


class _ModelListHandler(Handler):
    category = '_ma_model_list'

    def __init__(self, *args):
        super(_ModelListHandler, self).__init__(*args)
        # Map model_type to subclass of modelcif.model.Model
        self._type_map = _EnumerationMapper(
            modelcif.model, modelcif.model.Model,
            attr='model_type')

    def finalize(self):
        # Put all models not in a group in their own group
        models_in_groups = frozenset(m._id for mg in self.system.model_groups
                                     for m in mg)
        # Get ungrouped models in the order encountered in the file
        ungrouped = [m for m in self.sysr._all_seen_models
                     if m._id not in models_in_groups]
        if ungrouped:
            mg = modelcif.model.ModelGroup(ungrouped)
            self.system.model_groups.append(mg)

    def __call__(self, model_id, model_group_id, model_name, model_group_name,
                 assembly_id, data_id, model_type, model_type_other_details):
        if self.sysr.default_model_class:
            model_type = self._type_map.get(
                model_type, model_type_other_details)
            model = self.sysr.models.get_by_id(model_id, model_type)
        else:
            model = self.sysr.models.get_by_id(model_id)
            model.model_type = model_type
        mg = self.sysr.model_groups.get_by_id(model_group_id)
        mg.name = model_group_name
        model.name = model_name
        self.sysr.data_by_id[data_id] = model
        model._data_id = data_id
        model.assembly = self.sysr.assemblies.get_by_id(assembly_id)
        mg.append(model)


class _ProtocolHandler(Handler):
    category = '_ma_protocol_step'

    def __init__(self, *args):
        super(_ProtocolHandler, self).__init__(*args)
        # Map method_type to subclass of modelcif.protocol.Step
        self._method_map = dict(
            (x[1].method_type.upper(), x[1])
            for x in inspect.getmembers(modelcif.protocol, inspect.isclass)
            if issubclass(x[1], modelcif.protocol.Step)
            and x[1] is not modelcif.protocol.Step)

    def __call__(self, protocol_id, method_type, step_name, details,
                 software_group_id, input_data_group_id, output_data_group_id):
        p = self.sysr.protocols.get_by_id(protocol_id)
        stepcls = self._method_map.get(method_type.upper(),
                                       modelcif.protocol.Step)
        indata = self.sysr.data_groups.get_by_id(input_data_group_id)
        outdata = self.sysr.data_groups.get_by_id(output_data_group_id)
        software = self.sysr.software_groups.get_by_id_or_none(
            software_group_id)
        step = stepcls(input_data=indata, output_data=outdata, name=step_name,
                       details=details, software=software)
        p.steps.append(step)


def _make_qa_class(type_class, mode_class, p_name, p_description, p_software):
    """Create and return a new class to represent a QA metric"""
    class QA(type_class, mode_class):
        name = p_name
        __doc__ = p_description
        software = p_software
    QA.__name__ = p_name
    return QA


class _QAMetricHandler(Handler):
    category = '_ma_qa_metric'

    def __init__(self, *args):
        super(_QAMetricHandler, self).__init__(*args)
        # Map mode to subclass of modelcif.qa_metric.MetricMode
        self._mode_map = dict(
            (x[1].mode.upper(), x[1])
            for x in inspect.getmembers(modelcif.qa_metric, inspect.isclass)
            if issubclass(x[1], modelcif.qa_metric.MetricMode)
            and x[1] is not modelcif.qa_metric.MetricMode)
        # Map type to subclass of modelcif.qa_metric.MetricType
        # (also allow user-defined "other" classes)
        self._type_map = _EnumerationMapper(
            modelcif.qa_metric, modelcif.qa_metric.MetricType, attr="type")

    def __call__(self, id, name, description, type, mode, type_other_details,
                 software_group_id):
        type_class = self._type_map.get(type, type_other_details)
        mode_class = self._mode_map.get(mode.upper(),
                                        modelcif.qa_metric.MetricMode)
        software = self.sysr.software_groups.get_by_id_or_none(
            software_group_id)
        self.sysr.qa_by_id[id] = _make_qa_class(
            type_class, mode_class, name, description, software)


class _QAMetricGlobalHandler(Handler):
    category = '_ma_qa_metric_global'

    def __call__(self, model_id, metric_id, metric_value):
        model = self.sysr.models.get_by_id(model_id)
        metric_class = self.sysr.qa_by_id[metric_id]
        model.qa_metrics.append(metric_class(self.get_float(metric_value)))


class _QAMetricLocalHandler(Handler):
    category = '_ma_qa_metric_local'

    def __call__(self, model_id, label_asym_id, label_seq_id, metric_id,
                 metric_value):
        model = self.sysr.models.get_by_id(model_id)
        asym = self.sysr.asym_units.get_by_id(label_asym_id)
        seq_id = self.get_int(label_seq_id)
        residue = asym.residue(seq_id)
        metric_class = self.sysr.qa_by_id[metric_id]
        model.qa_metrics.append(metric_class(residue,
                                             self.get_float(metric_value)))


class _QAMetricPairwiseHandler(Handler):
    category = '_ma_qa_metric_local_pairwise'

    def __call__(self, model_id, label_asym_id_1, label_seq_id_1,
                 label_asym_id_2, label_seq_id_2, metric_id, metric_value):
        model = self.sysr.models.get_by_id(model_id)
        asym1 = self.sysr.asym_units.get_by_id(label_asym_id_1)
        seq_id1 = self.get_int(label_seq_id_1)
        residue1 = asym1.residue(seq_id1)
        asym2 = self.sysr.asym_units.get_by_id(label_asym_id_2)
        seq_id2 = self.get_int(label_seq_id_2)
        residue2 = asym2.residue(seq_id2)
        metric_class = self.sysr.qa_by_id[metric_id]
        model.qa_metrics.append(metric_class(residue1, residue2,
                                             self.get_float(metric_value)))


class ModelCIFVariant(Variant):
    """Used to select typical PDBx/ModelCIF file input.
       See :func:`read` and :class:`ihm.reader.Variant`."""
    system_reader = _SystemReader

    _handlers = [
        ihm.reader._StructHandler, ihm.reader._SoftwareHandler,
        ihm.reader._CitationHandler, ihm.reader._AuditAuthorHandler,
        ihm.reader._GrantHandler, ihm.reader._CitationAuthorHandler,
        ihm.reader._ChemCompHandler, ihm.reader._EntityHandler,
        ihm.reader._EntitySrcNatHandler, ihm.reader._EntitySrcGenHandler,
        ihm.reader._EntitySrcSynHandler, ihm.reader._EntityPolyHandler,
        ihm.reader._EntityPolySeqHandler, ihm.reader._EntityNonPolyHandler,
        ihm.reader._StructAsymHandler, _SoftwareGroupHandler,
        _DatabaseHandler, _SoftwareParameterHandler,
        _DataHandler, _DataGroupHandler, _TargetEntityHandler,
        _TargetRefDBHandler, _TransformationHandler, _TemplateDetailsHandler,
        _TemplateRefDBHandler, _TemplatePolySegmentHandler,
        _AlignmentHandler, _AlignmentInfoHandler, _AlignmentDetailsHandler,
        _TargetTemplatePolyMappingHandler,
        _AssemblyHandler, _AssemblyDetailsHandler, ihm.reader._AtomSiteHandler,
        _ModelListHandler, _ProtocolHandler, _QAMetricHandler,
        _QAMetricGlobalHandler, _QAMetricLocalHandler,
        _QAMetricPairwiseHandler]

    def get_handlers(self, sysr):
        return [h(sysr) for h in self._handlers]

    def get_audit_conform_handler(self, sysr):
        return _AuditConformHandler(sysr)


def read(fh, model_class=modelcif.model.Model, format='mmCIF', handlers=[],
         warn_unknown_category=False, warn_unknown_keyword=False,
         reject_old_file=False, variant=ModelCIFVariant):
    """Read data from the file handle `fh`.

       See :func:`ihm.reader.read` for more information. The function
       here behaves similarly but reads in files compliant with the
       ModelCIF extension directory rather than IHM.

       Note that if a custom ``model_class`` is provided, any models present
       in the file will be returned as that type, regardless of their type
       stated in the mmCIF file (e.g. homology model, ab initio model).
       (However, the ``model_type`` attribute will be set appropriately.)

      :return: A list of :class:`modelcif.System` objects.
    """
    return ihm.reader.read(
        fh, model_class=model_class, format=format, handlers=handlers,
        warn_unknown_category=warn_unknown_category,
        warn_unknown_keyword=warn_unknown_keyword,
        reject_old_file=reject_old_file, variant=variant)
