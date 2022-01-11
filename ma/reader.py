import ma
import ma.model
import ma.protocol
import ihm
import ihm.source
import ihm.reader
from ihm.reader import Variant, Handler, IDMapper, _ChemCompIDMapper
from ihm.reader import OldFileError, _make_new_entity
import inspect


class _AuditConformHandler(Handler):
    category = '_audit_conform'

    def __call__(self, dict_name, dict_version):
        # Reject old file versions if we can parse the version
        if dict_name == "mmcif_ma.dic":
            try:
                major, minor, _ = [int(x) for x in dict_version.split('.')]
                if (major, minor) < (1, 3):
                    raise OldFileError(
                        "This version of python-ma only supports reading "
                        "files that conform to version 1.3 or later of the "
                        "MA extension dictionary. This file conforms to "
                        "version %s." % dict_version)
            except ValueError:
                pass


class _SystemReader(object):
    def __init__(self, model_class, starting_model_class):
        self.system = ma.System()

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
                                        ma.SoftwareGroup)

        self.data_by_id = {}
        self.data_groups = IDMapper(self.system.data_groups, ma.data.DataGroup)

        self.transformations = IDMapper(self.system.template_transformations,
                                        ma.Transformation, *(None,) * 2)

        self.templates = IDMapper(self.system.templates, ma.Template,
                                  *(None,) * 4)

        self.template_segments = IDMapper(
            self.system.template_segments, ma.TemplateSegment, *(None,) * 4)

        self.models = IDMapper(None, model_class, [], None)

        self.model_groups = IDMapper(self.system.model_groups,
                                     ma.model.ModelGroup)

        self.assemblies = IDMapper(self.system.assemblies, ma.Assembly)

        self.protocols = IDMapper(self.system.protocols, ma.protocol.Protocol)

    def finalize(self):
        # make sequence immutable (see also _make_new_entity)
        for e in self.system.entities:
            e.sequence = tuple(e.sequence)


class _SoftwareGroupHandler(Handler):
    category = '_ma_software_group'

    def __call__(self, group_id, software_id):
        g = self.sysr.software_groups.get_by_id(group_id)
        s = self.sysr.software.get_by_id(software_id)
        g.append(s)


class _DataGroupHandler(Handler):
    category = '_ma_data_group'

    def __call__(self, group_id, data_id):
        g = self.sysr.data_groups.get_by_id(group_id)
        # fill in real Data objects at finalize time
        g.append(data_id)

    def finalize(self):
        for g in self.system.data_groups:
            # todo: return Data placeholder if Model/Template/etc. object
            # not available for a given id?
            g[:] = [self.sysr.data_by_id.get(x) for x in g]


class _EnumerationMapper(object):
    """Map an mmCIF enumerated value to the corresponding Python class"""
    def __init__(self, module, base_class):
        self._base_class = base_class
        self._other_name = base_class.name.upper()
        self._map = dict(
            (x[1].name.upper(), x[1])
            for x in inspect.getmembers(module, inspect.isclass)
            if issubclass(x[1], base_class) and x[1] is not base_class)
        self._other_map = {}

    def get(self, nam, other_det):
        """Get the Python class that matches the given name
           and other_details"""
        nam = nam.upper()
        typ = self._map.get(nam)
        if typ:
            return typ
        # If name is not Other this is an enumeration value we don't have
        # a class for; make and cache a new class for the given name:
        if nam != self._other_name:
            class ExtraType(self._base_class):
                name = nam
                other_details = None
            self._map[nam] = ExtraType
            return ExtraType
        # If name is "Other" then treat other_details as the key
        other_det_up = other_det.upper()
        if other_det_up not in self._other_map:
            class CustomType(self._base_class):
                other_details = other_det
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
        # Map db_name to subclass of ma.reference.TargetReference
        self.type_map = _EnumerationMapper(ma.reference,
                                           ma.reference.TargetReference)

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
        # Map db_name to subclass of ma.reference.TemplateReference
        self.type_map = _EnumerationMapper(ma.reference,
                                           ma.reference.TemplateReference)

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
        if isinstance(comp, ma.AsymUnitRange) \
           and comp.seq_id_range == comp.asym.seq_id_range:
            return comp.asym
        else:
            return comp


class _ModelListHandler(Handler):
    category = '_ma_model_list'

    def __call__(self, model_id, model_group_id, model_name, model_group_name,
                 assembly_id, data_id, model_type, model_type_other_details):
        mg = self.sysr.model_groups.get_by_id(model_group_id)
        mg.name = model_group_name
        model = self.sysr.models.get_by_id(model_id)
        model.name = model_name
        self.sysr.data_by_id[data_id] = model
        model._data_id = data_id
        model.assembly = self.sysr.assemblies.get_by_id(assembly_id)
        mg.append(model)
        # todo: handle other fields


class _ProtocolHandler(Handler):
    category = '_ma_protocol_step'

    def __init__(self, *args):
        super(_ProtocolHandler, self).__init__(*args)
        # Map method_type to subclass of ma.protocol.Step
        self._method_map = dict(
            (x[1].method_type.upper(), x[1])
            for x in inspect.getmembers(ma.protocol, inspect.isclass)
            if issubclass(x[1], ma.protocol.Step)
            and x[1] is not ma.protocol.Step)

    def __call__(self, protocol_id, method_type, step_name, details,
                 software_group_id, input_data_group_id, output_data_group_id):
        p = self.sysr.protocols.get_by_id(protocol_id)
        stepcls = self._method_map.get(method_type.upper(), ma.protocol.Step)
        indata = self.sysr.data_groups.get_by_id(input_data_group_id)
        outdata = self.sysr.data_groups.get_by_id(output_data_group_id)
        software = self.sysr.software_groups.get_by_id_or_none(
            software_group_id)
        step = stepcls(input_data=indata, output_data=outdata, name=step_name,
                       details=details, software=software)
        p.steps.append(step)


class ModelArchiveVariant(Variant):
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
        _DataGroupHandler, _TargetEntityHandler,
        _TargetRefDBHandler, _TransformationHandler, _TemplateDetailsHandler,
        _TemplateRefDBHandler, _TemplatePolySegmentHandler,
        _AssemblyHandler, ihm.reader._AtomSiteHandler,
        _ModelListHandler, _ProtocolHandler]

    def get_handlers(self, sysr):
        return [h(sysr) for h in self._handlers]

    def get_audit_conform_handler(self, sysr):
        return _AuditConformHandler(sysr)


def read(fh, model_class=ma.model.Model, format='mmCIF', handlers=[],
         warn_unknown_category=False, warn_unknown_keyword=False,
         reject_old_file=False, variant=ModelArchiveVariant):
    return ihm.reader.read(
        fh, model_class=model_class, format=format, handlers=handlers,
        warn_unknown_category=warn_unknown_category,
        warn_unknown_keyword=warn_unknown_keyword,
        reject_old_file=reject_old_file, variant=variant)
