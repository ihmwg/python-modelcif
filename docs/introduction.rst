Introduction
************

This package provides a mechanism to describe the generation of a
theoretical model (for example, via comparative or homology model)
a set of Python objects. This includes, if applicable

 - the templates(s) used for the modeling;
 - the alignment between the template(s) and target sequence;
 - the protocol used to generate models, such as template search, modeling,
   and model selection;
 - the actual coordinates of output models;
 - grouping of multiple models;
 - quality scores for models and/or alignments.

Once created, this set of Python objects can be written to an mmCIF file
that is compliant with the
`ModelCIF extension <https://github.com/ihmwg/ModelCIF>`_
to the `PDBx/mmCIF dictionary <http://mmcif.wwpdb.org/>`_,
suitable for deposition in a repository such as
`ModelArchive <https://modelarchive.org/>`_. The files can be viewed in any
regular PDBx mmCIF viewer, such as
`UCSF ChimeraX <https://www.cgl.ucsf.edu/chimerax/>`_ (although most viewers
to date will only show the model coordinates, not the ModelCIF-specific
metadata).
