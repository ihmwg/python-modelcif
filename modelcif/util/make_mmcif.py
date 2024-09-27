#!/usr/bin/env python3

"""
Add minimal ModelCIF-related tables to an mmCIF file.

Given any mmCIF file as input, this script will add any missing
ModelCIF-related tables and write out a new file that is minimally compliant
with the ModelCIF dictionary.

This is done by simply reading in the original file with python-modelcif and
then writing it out again, so
  a) any data in the input file that is not understood by python-modelcif
     will be lost on output; and
  b) input files that aren't compliant with the PDBx dictionary, or that
     contain syntax errors or other problems, may crash or otherwise confuse
     python-modelcif.
"""


import modelcif.reader
import modelcif.dumper
import modelcif.model
import ihm.util
import os
import argparse


def add_modelcif_info(s):
    if not s.title:
        s.title = 'Auto-generated system'

    for model_group in s.model_groups:
        for model in model_group:
            model.not_modeled_residue_ranges.extend(
                _get_not_modeled_residues(model))
    return s


def _get_not_modeled_residues(model):
    """Yield NotModeledResidueRange objects for all residue ranges in the
       Model that are not referenced by Atom, Sphere, or pre-existing
       NotModeledResidueRange objects"""
    for assem in model.assembly:
        asym = assem.asym if hasattr(assem, 'asym') else assem
        if not asym.entity.is_polymeric():
            continue
        # Make a set of all residue indices of this asym "handled" either
        # by being modeled (with Atom or Sphere objects) or by being
        # explicitly marked as not-modeled
        handled_residues = set()
        for rr in model.not_modeled_residue_ranges:
            if rr.asym_unit is asym:
                for seq_id in range(rr.seq_id_begin, rr.seq_id_end + 1):
                    handled_residues.add(seq_id)
        for atom in model._atoms:
            if atom.asym_unit is asym:
                handled_residues.add(atom.seq_id)
        # Convert set to a list of residue ranges
        handled_residues = ihm.util._make_range_from_list(
            sorted(handled_residues))
        # Return not-modeled for each non-handled range
        for r in ihm.util._invert_ranges(handled_residues,
                                         end=assem.seq_id_range[1],
                                         start=assem.seq_id_range[0]):
            yield modelcif.model.NotModeledResidueRange(asym, r[0], r[1])


def get_args():
    p = argparse.ArgumentParser(
        description="Add minimal ModelCIF-related tables to an mmCIF file.")
    p.add_argument("input", metavar="input.cif", help="input mmCIF file name")
    p.add_argument("output", metavar="output.cif",
                   help="output mmCIF file name",
                   default="output.cif", nargs="?")
    return p.parse_args()


def main():
    args = get_args()

    if (os.path.exists(args.input) and os.path.exists(args.output)
            and os.path.samefile(args.input, args.output)):
        raise ValueError("Input and output are the same file")

    with open(args.input) as fh:
        with open(args.output, 'w') as fhout:
            modelcif.dumper.write(
                fhout,
                [add_modelcif_info(s) for s in modelcif.reader.read(fh)])


if __name__ == '__main__':
    main()
