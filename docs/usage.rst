Usage
*****

Usage of the library for output consists of first creating a hierarchy of
Python objects that together describe the system, and then dumping that
hierarchy to an mmCIF or BinaryCIF file.

For a complete worked example, see the
`ModBase example <https://github.com/ihmwg/python-ma/blob/main/examples/mkmodbase.py>`_.

The top level of the hierarchy is the :class:`ma.System`. All other
objects are referenced from a System object (either directly or via another
object that is referenced by the System).

System architecture
===================

The architecture of the system is described with a number of classes:

 - :class:`ma.Entity` describes each unique sequence (used in the target
   model, in one or more templates, or both).
 - :class:`ma.AsymUnit` describes each asymmetric unit (chain) in the target
   model. For example, a homodimer would consist of two asymmetric units, both
   pointing to the same entity, while a heterodimer contains two entities.
 - Similarly, :class:`ma.Template` describes a chain used as a template.
 - :class:`ma.Assembly` groups asymmetric units, or parts of
   them. Assemblies are used to describe which parts of the system were modeled.
 - A variety of classes in the :mod:`ma.alignment` module can be used to
   describe alignments between the target and one or more templates.

Modeling protocol
=================

:class:`ma.protocol.Protocol` objects describe how models were generated
from the input data. A protocol can consist of
:class:`multiple steps <ma.protocol.Step>`, such as template search, alignment,
modeling, and model selection. These objects also describe what was used as
input and what was generated on output by each step, as one or more
:class:`ma.data.Data` objects.

Model coordinates
=================

:class:`ma.model.Model` objects give the actual coordinates of the final
generated models. These point to the :class:`~ma.Assembly` of what was
modeled. Quality scores can also be assigned to each model (see the
:mod:`ma.qa_metric` module) or to individual residues or pairs of residues.

Models can also be grouped together for any purpose using the
:class:`ma.model.ModelGroup` class.

Metadata
========

Metadata can also be added to the system, such as

 - :attr:`ma.System.citations`: publication(s) that describe this modeling
   or the methods used in it.
 - :class:`ma.Software`: software packages used at any stage in the modeling.
 - :attr:`ma.System.grants`: funding support for the modeling.
 - :class:`ma.reference.TemplateReference`: or
   :class:`ma.reference.TargetReference`: information on a template
   structure, or a target sequence.

Residue numbering
=================

The library keeps track of several numbering schemes to reflect the reality
of the data used in modeling:

 - *Internal numbering*. Residues are always numbered sequentially starting at
   1 in an :class:`~ma.Entity`. All references to residues or residue ranges in
   the library use this numbering.
 - *Author-provided numbering*. If a different numbering scheme is used by the
   authors, for example to correspond to the numbering of the original sequence
   that is modeled, this can be given as an author-provided numbering for
   one or more asymmetric units. See the ``auth_seq_id_map`` parameter to
   :class:`~ma.AsymUnit`. (The mapping between author-provided and internal
   numbering is given in the ``pdbx_poly_seq_scheme`` table in the mmCIF file.)

Output
======

Once the hierarchy of classes is complete, it can be freely inspected or
modified. All the classes are simple lightweight Python objects, generally
with the relevant data available as member variables.

The complete hierarchy can be written out to an mmCIF or BinaryCIF file using
the :func:`ma.dumper.write` function.

Input
=====

Hierarchies of classes can also be read from mmCIF or BinaryCIF files.
This is done using the :func:`ma.reader.read` function, which returns a list of
:class:`ma.System` objects.
