import ma
import ma.model
import ihm.reader
from ihm.reader import Variant, Handler, _SystemReaderBase, IDMapper
from ihm.reader import OldFileError

class _AuditConformHandler(Handler):
    category = '_audit_conform'

    def __call__(self, dict_name, dict_version):
        # Reject old file versions if we can parse the version
        if dict_name == "mmcif_ma.dic":
            try:
                major, minor, _ = [int(x) for x in dict_version.split('.')]
                if (major, minor) < (1,3):
                    raise OldFileError(
                        "This version of python-ma only supports reading "
                        "files that conform to version 1.3 or later of the "
                        "MA extension dictionary. This file conforms to "
                        "version %s." % dict_version)
            except ValueError:
                pass


class SystemReader(_SystemReaderBase):
    def __init__(self, model_class, starting_model_class):
        self.system = ma.System()

        super(SystemReader, self).__init__(model_class, starting_model_class)

        self.software_groups = IDMapper(self.system.software_groups,
                                        ma.SoftwareGroup)


class _SoftwareGroupHandler(Handler):
    category = '_ma_software_group'

    def __call__(self, group_id, software_id):
        g = self.sysr.software_groups.get_by_id(group_id)
        s = self.sysr.software.get_by_id(software_id)
        g.append(s)


class ModelArchiveVariant(Variant):
    system_reader = SystemReader

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

