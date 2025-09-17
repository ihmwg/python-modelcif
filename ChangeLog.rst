1.5 - 2025-09-17
================
  - The ``pdbx_nonpoly_scheme`` and ``pdbx_poly_seq_scheme``
    tables are now read from and written to mmCIF or BinaryCIF
    files. This allows for files containing waters to be
    correctly processed (#52).
  - A ``pyproject.toml`` file is now provided for compatibility
    with modern versions of pip (#50).
  - Bugfix: the ``is_primary`` attribute of
    :class:`modelcif.reference.TargetReference` is now correctly
    set when reading files containing a ``_struct_ref`` table
    but no ``_ma_target_ref_db_details`` table (#51).

1.4 - 2025-06-11
================
  - Revision information and information on how the data in the file can
    be used are now read from or written to mmCIF or BinaryCIF files.
    See :attr:`System.revisions` and :attr:`System.data_usage` respectively.
  - New classes have been added to :mod:`modelcif.alignment`,
    :mod:`modelcif.qa_metric`, and :mod:`modelcif.protocol` to support
    all sequence identity denominators (#47), QA metric types (#45),
    and protocol step types (#44) respectively, as defined in the ModelCIF
    dictionary.
  - The new :class:`modelcif.alignment.Local` and
    :class:`modelcif.alignment.Multiple` classes allow for both local
    alignments and multiple sequence alignments to be described (#43).
  - Bugfix: sequence identity and alignment score (``identity`` and ``score``
    arguments to :class:`modelcif.alignment.Pair`) are now optional, to
    match the mmCIF dictionary (#49).
  - Bugfix: information in ``_ma_template_non_poly.details`` is now read
    from mmCIF or BinaryCIF files (#48).
  - Bugfix: files containing empty or missing ``_ma_qa_metric.description``
    can now be read (#46).

1.3 - 2025-01-14
================
  - The new :class:`modelcif.CustomTemplate` class allows for custom templates
    (that have not been deposited in a database such as PDB) to be referenced,
    together with their atomic coordinates (#1).
  - Model quality scores can now be defined that act on single features or
    pairs of features using the :class:`modelcif.qa_metric.Feature` and
    :class:`modelcif.qa_metric.FeaturePairwise` classes, respectively.
    Features can be defined as groups of atoms, residues, or asyms (#38).
  - The :class:`modelcif.associated.QAMetricsFile` class should now be used
    to reference files that contain model quality scores. The old name
    (LocalPairwiseQAScoresFile) is deprecated. This allows for all types of
    QA scores, not just local pairwise scores, to be stored in a separate file.
  - Sanity checks when writing out a file can now be disabled if desired,
    using the new ``check`` argument to :func:`modelcif.dumper.write`.
  - :class:`modelcif.reference.TargetReference` now takes an ``is_primary``
    argument which can be used to denote the most pertinent sequence
    database reference.
  - Information on model groups (:class:`modelcif.model.ModelGroup`) is now
    written to the new ``ma_model_group`` and ``ma_model_group_link`` mmCIF
    tables, instead of ``ma_model_list``, to match the latest ModelCIF
    dictionary. Old-style information in ``ma_model_list`` will still be
    used when reading a file if these new tables are missing.

1.2 - 2024-10-23
================
  - Data that have been split over multiple mmCIF or BinaryCIF files can now
    be combined into a single :class:`modelcif.System` object using the new
    ``add_to_system`` argument to :func:`modelcif.reader.read` (#10).
  - A new example, ``associated.py``, has been added to demonstrate reading
    in data that has been split into multiple "associated" mmCIF files using
    :class:`modelcif.associated.CIFFile`.

1.1 - 2024-09-27
================
 - The new class :class:`modelcif.model.NotModeledResidueRange` allows for
   the annotation of residue ranges that were explicitly not modeled.
   Any residue marked as not-modeled in all models will be excluded from
   the ``pdbx_poly_seq_scheme`` table.
 - The ``util/make-mmcif.py`` script is now included in the installed package,
   so can be run if desired with ``python3 -m modelcif.util.make_mmcif``.
 - The ``make_mmcif`` utility script will now automatically add any
   missing :class:`modelcif.model.NotModeledResidueRange` objects for
   not-modeled residue ranges.

1.0 - 2024-06-20
================
 - Reference information in the ``struct_ref`` mmCIF table is now supported
   in addition to the ModelCIF-specific tables such as
   ``ma_target_ref_db_details``. :class:`modelcif.reference.TargetReference`
   now inherits from ``ihm.reference.Sequence`` and allows for the full
   database sequence, plus any differences between it and the modeled sequence,
   to be recorded. The ``align_begin`` and ``align_end`` arguments are now
   deprecated (#34).

0.9 - 2023-10-02
================
 - Bugfix: :class:`modelcif.SoftwareGroup` now allows for parameters to
   be associated with each piece of software in the group, rather than
   with the group as a whole (#33).

0.8 - 2023-08-04
================
 - :class:`modelcif.associated.File` now takes an optional ``data``
   argument to allow describing any modeling input/output that is stored
   in that file.
 - RPM packages are now provided for Fedora and RedHat Enterprise Linux.

0.7 - 2023-01-25
================
 - More examples have been added to demonstrate interconversion between
   mmCIF and BinaryCIF, and to validate mmCIF files.
 - A utility script ``util/make-mmcif.py`` has been added which can add
   minimal ModelCIF-related tables to an mmCIF file, to add in deposition.
 - The reader is now more robust when handling files that are not ModelCIF
   compliant (#31).
 - The ``exptl`` table is no longer written to output mmCIF files, to conform
   with wwPDB's recommendation. Instead, the
   ``struct.pdbx_structure_determination_methodology`` data item denotes
   that the model is computational (#29).

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
   :class:`modelcif.alignment.HHblitsEValue`.
