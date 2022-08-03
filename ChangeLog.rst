0.6 - 2022-08-03
================
 - :class:`ihm.ChemComp` now allows for custom chemical components to be
   defined in a chemical component dictionary (CCD) outside of the wwPDB CCD,
   such as the ModelArchive CCD, or in the file itself using descriptors such
   as SMILES or InChI in the :mod:`modelcif.descriptor` module.
 - The ``ma_struct_assembly`` category is no longer written out to mmCIF
   files, as this is deprecated by ModelCIF (all models are required to
   have the same composition).
 - Templates can now be described in AlphaFoldDB or PubChem using new
   :class:`modelcif.reference.TemplateReference` subclasses.
 - HHblits e-values can now be used as alignment scores, using
   :class:`modelcif.alignment.HHblitsEValue`.
 - Bugfix: :class:`modelcif.associated.CIFFile` now writes local files
   (if requested via ``categories`` or ``copy_categories``) even if it
   is placed inside a :class:`modelcif.associated.ZipFile` (#26).

0.5 - 2022-05-10
================
 - A new class :class:`modelcif.ReferenceDatabase` allows describing
   collections of sequences that were used as part of the modeling protocol.
 - Lists of ints or floats can now be given as software parameters to the
   :class:`modelcif.SoftwareParameter` class.

0.4 - 2022-04-14
================
 - Sequence information for templates is now only written to template-specific
   categories in the mmCIF/BinaryCIF, not to the entity, entity_poly etc.
   tables, to properly comply with the ModelCIF dictionary.
 - :class:`modelcif.Template` now takes a ``entity_id`` argument which can be
   used to provide the entity ID (if known) of the template in its own mmCIF
   file.
 - External files (e.g. alignments, or quality scores) can now be referenced
   from the main file (using the :mod:`modelcif.associated` module). Selected
   CIF categories can automatically be written to these external files instead
   of the main file, in either mmCIF or BinaryCIF format (see
   :class:`modelcif.associated.CIFFile`).
 - Non-polymer models can now be linked to their template using the
   :class:`modelcif.NonPolymerFromTemplate` class.
 - Add classes for the PLDDT, PTM, and IpTM quality metrics.
 - :class:`modelcif.reference.TargetReference` now supports the version
   and CRC64 checksum of the reference sequence.

0.3 - 2022-03-21
================
 - Add a package to conda-forge so the library can be installed using
   ``conda install -c conda-forge modelcif``
 - :class:`modelcif.Template` now takes a ``strand_id`` argument which can
   be used to provide the author-provided (e.g. PDB) chain ID.
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
