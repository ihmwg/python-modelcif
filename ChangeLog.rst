0.3 - 2022-03-21
================
 - Add a package to conda-forge so the library can be installed using
   ``conda install -c conda-forge modelcif``
 - :class:`modelcif.Template` now takes a ``strand_id`` argument which can
   be used to provided the author-provided (e.g. PDB) chain ID.
 - Non-polymers can now be used as templates.

0.2 - 2022-01-27
================
 - Minor packaging and documentation improvements.
 - Add a basic "theoretical model" exptl category to output files.
 - Bugfix: fix output of alignments with an empty list of pairs.

0.1 - 2022-01-26
================
 - First stable release. This provides support for single-chain single-template
   models using the ModelCIF extension dictionary, and will read and
   write mmCIF and BinaryCIF files that are compliant with the PDBx and
   ModelCIF dictionaries.
