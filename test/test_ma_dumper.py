import utils
import os
import unittest
import sys
if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from io import BytesIO as StringIO

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import ma.dumper
import ma.protocol
import ihm.format


def _get_dumper_output(dumper, system):
    fh = StringIO()
    writer = ihm.format.CifWriter(fh)
    dumper.dump(system, writer)
    return fh.getvalue()


class Tests(unittest.TestCase):
    def test_audit_conform_dumper(self):
        """Test AuditConformDumper"""
        system = ma.System()
        dumper = ma.dumper._AuditConformDumper()
        out = _get_dumper_output(dumper, system)
        lines = sorted(out.split('\n'))
        self.assertEqual(lines[1].split()[0], "_audit_conform.dict_location")
        self.assertEqual(lines[2].rstrip('\r\n'),
                         "_audit_conform.dict_name mmcif_ma.dic")
        self.assertEqual(lines[3].split()[0], "_audit_conform.dict_version")

    def test_software_group_dumper(self):
        """Test SoftwareGroupDumper"""
        class MockObject(object):
            pass
        s1 = ma.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._id = 1
        s2 = ma.Software(
            name='s2', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s2._id = 2
        s3 = ma.Software(
            name='s3', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s3._id = 3
        system = ma.System()
        aln1 = MockObject()
        aln1.software = ma.SoftwareGroup((s1, s2))
        aln2 = MockObject()
        aln2.software = s3
        system.alignments.extend((aln1, aln2))
        dumper = ma.dumper._SoftwareGroupDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        # Should have one group (s1, s2) and another singleton group (s3)
        self.assertEqual(out, """#
loop_
_ma_software_group.ordinal_id
_ma_software_group.group_id
_ma_software_group.software_id
_ma_software_group.parameter_group_id
1 1 1 .
2 1 2 .
3 2 3 .
#
""")

    def test_data_dumper(self):
        """Test DataDumper"""
        system = ma.System()
        entity = ma.Entity("DMA")
        system.entities.append(entity)
        asym = ma.AsymUnit(entity, name="test asym")
        system.asym_units.append(asym)
        template = ma.Template(entity, asym_id="A", model_num=1,
                               name="test template")
        system.templates.append(template)
        system.templates.append(ma.data.Data(name="test other",
                                             details="test details"))
        dumper = ma.dumper._DataDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_data.id
_ma_data.name
_ma_data.content_type
_ma_data.content_type_other_details
1 'test template' 'template structure' .
2 'test other' other 'test details'
3 'test asym' target .
#
""")

    def test_data_group_dumper(self):
        """Test DataGroupDumper"""
        system = ma.System()
        entity = ma.Entity("DMA")
        system.entities.append(entity)
        asym1 = ma.AsymUnit(entity, name="test asym1")
        asym1._data_id = 1
        asym2 = ma.AsymUnit(entity, name="test asym2")
        asym2._data_id = 2
        asym3 = ma.AsymUnit(entity, name="test asym3")
        asym3._data_id = 3
        system.asym_units.extend((asym1, asym2, asym3))
        dg12 = ma.data.DataGroup((asym1, asym2))
        p = ma.protocol.Protocol()
        p.steps.append(ma.protocol.ModelingStep(
            input_data=dg12, output_data=asym3))
        system.protocols.append(p)
        dumper = ma.dumper._DataGroupDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        # First group (asym1,asym2); second group contains just asym3
        self.assertEqual(out, """#
loop_
_ma_data_group.ordinal_id
_ma_data_group.group_id
_ma_data_group.data_id
1 1 1
2 1 2
3 2 3
#
""")


if __name__ == '__main__':
    unittest.main()
