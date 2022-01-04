import ma
import ma.model
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

        self.transformations = IDMapper(self.system.template_transformations,
                                        ma.Transformation, *(None,) * 2)

        self.templates = IDMapper(self.system.templates, ma.Template,
                                  *(None,) * 4)

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
        # todo: fill in target_asym_id in alignment
        # todo: fill in data_id


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
        _TargetRefDBHandler, _TransformationHandler, _TemplateDetailsHandler]

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
