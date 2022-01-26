.. _limitations:

.. currentmodule:: modelcif

Limitations
***********

By design the library maps the PDBx/ModelCIF data model to its own hierarchy
of Python objects. This hierarchy does not cover every possible mmCIF
category; thus, the library is not necessarily preserving of file contents
(e.g. if a file is read in and then a new file is written out, categories or
data items from the original file not understood by the library will be
missing in the new file).

In particular, many PDBx categories pertaining to experimentally-determined
structures are ignored. Also, the following ModelCIF categories are currently
not supported:

 - ``ma_template_non_poly``
 - ``ma_template_customized``
 - ``ma_template_coord``
 - ``ma_coevolution_seq_db_ref``
 - ``ma_coevolution_msa``
 - ``ma_coevolution_msa_details``
 - ``ma_restraints``
 - ``ma_distance_restraints``
 - ``ma_angle_restraints``
 - ``ma_dihedral_restraints``
 - ``ma_restraints_group``
 - ``ma_poly_template_library_details``
 - ``ma_poly_template_library_list``
 - ``ma_poly_template_library_components``
 - ``ma_entry_associated_files``
 - ``ma_associated_archive_file_details``
