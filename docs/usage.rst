Usage
*****

Usage of the library for output consists of first creating a hierarchy of
Python objects that together describe the system, and then dumping that
hierarchy to an mmCIF or BinaryCIF file.

For complete worked examples, see the
`ModBase example <https://github.com/ihmwg/python-ma/blob/main/examples/mkmodbase.py>`_
or the
`ligands example <https://github.com/ihmwg/python-modelcif/blob/main/examples/ligands.py>`_.

The top level of the hierarchy is the :class:`modelcif.System`. All other
objects are referenced from a System object (either directly or via another
object that is referenced by the System).

System architecture
===================

The architecture of the system is described with a number of classes:

 - :class:`modelcif.Entity` describes each unique sequence (used in the target
   model, in one or more templates, or both).
 - :class:`modelcif.AsymUnit` describes each asymmetric unit (chain) in the
   target model. For example, a homodimer would consist of two asymmetric
   units, both pointing to the same entity, while a heterodimer contains
   two entities.
 - Similarly, :class:`modelcif.Template` describes a chain used as a template.
 - :class:`modelcif.Assembly` groups asymmetric units, or parts of
   them. Assemblies are used to describe which parts of the system were modeled.
 - A variety of classes in the :mod:`modelcif.alignment` module can be used to
   describe alignments between the target and one or more templates.

Modeling protocol
=================

:class:`modelcif.protocol.Protocol` objects describe how models were generated
from the input data. A protocol can consist of
:class:`multiple steps <modelcif.protocol.Step>`, such as template search,
alignment, modeling, and model selection. These objects also describe what
was used as input and what was generated on output by each step, as one or more
:class:`modelcif.data.Data` objects.

Model coordinates
=================

:class:`modelcif.model.Model` objects give the actual coordinates of the final
generated models. These point to the :class:`~modelcif.Assembly` of what was
modeled. Quality scores can also be assigned to each model (see the
:mod:`modelcif.qa_metric` module) or to individual residues or pairs
of residues.

Models can also be grouped together for any purpose using the
:class:`modelcif.model.ModelGroup` class.

Metadata
========

Metadata can also be added to the system, such as

 - :attr:`modelcif.System.citations`: publication(s) that describe this modeling
   or the methods used in it.
 - :class:`modelcif.Software`: software packages used at any stage in the
   modeling.
 - :attr:`modelcif.System.grants`: funding support for the modeling.
 - :class:`modelcif.reference.TemplateReference`: or
   :class:`modelcif.reference.TargetReference`: information on a template
   structure, or a target sequence.

Residue numbering
=================

The library keeps track of several numbering schemes to reflect the reality
of the data used in modeling:

 - *Internal numbering*. Residues are always numbered sequentially starting at
   1 in an :class:`~modelcif.Entity`. All references to residues or residue
   ranges in the library use this numbering.
 - *Author-provided numbering*. If a different numbering scheme is used by the
   authors, for example to correspond to the numbering of the original sequence
   that is modeled, this can be given as an author-provided numbering for
   one or more asymmetric units. See the ``auth_seq_id_map`` parameter to
   :class:`~modelcif.AsymUnit`. (The mapping between author-provided and
   internal numbering is given in the ``pdbx_poly_seq_scheme`` table in
   the mmCIF file.)

Output
======

Once the hierarchy of classes is complete, it can be freely inspected or
modified. All the classes are simple lightweight Python objects, generally
with the relevant data available as member variables.

The complete hierarchy can be written out to an mmCIF or BinaryCIF file using
the :func:`modelcif.dumper.write` function.

Input
=====

Hierarchies of classes can also be read from mmCIF or BinaryCIF files.
This is done using the :func:`modelcif.reader.read` function, which returns
a list of :class:`modelcif.System` objects.

Format conversion
=================

The library can be employed to easily convert a ModelCIF file between mmCIF
and BinaryCIF format by simply reading in one format and then writing in
another. See the
`convert_bcif example <https://github.com/ihmwg/python-modelcif/blob/main/examples/convert_bcif.py>`_.

Conversion from legacy PDB format to mmCIF or BinaryCIF is not generally
possible because PDB format has no defined standard for including information
about modeling protocols, alignments, and so on. This extra information must be
deduced from other sources, for example custom PDB REMARK records or separate
files, and provided to the library. For reference, a script that uses the
library to convert `ModBase <https://modbase.compbio.ucsf.edu/>`_ models from
PDB format to mmCIF can be
`seen here <https://github.com/salilab/modbase_utils/blob/main/modbase_pdb_to_cif.py>`_.

Validation
==========

The library is designed to generate files that are consistent with the
`PDBx <https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Index/>`_
and `ModelCIF <https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Index/>`_
dictionaries by construction. However, the library can also be used to validate
ModelCIF (or other mmCIF/BinaryCIF files) if desired; see the
`validator example <https://github.com/ihmwg/python-modelcif/blob/main/examples/validate_mmcif.py>`_.
