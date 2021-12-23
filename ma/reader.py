import ma
import ma.model
import ihm
import ihm.source
import ihm.reader
from ihm.reader import Variant, Handler, IDMapper, _ChemCompIDMapper
from ihm.reader import OldFileError, _make_new_entity


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
        ihm.reader._StructAsymHandler, _SoftwareGroupHandler]

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
