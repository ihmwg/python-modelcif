# This example demonstrates reading ModelCIF "associated" files.
# Some repositories, such as ModelArchive, split the deposited data into
# multiple mmCIF files, putting some of the quality score information not
# into the main mmCIF file but into a separate "associated" file.
# These associated files are referenced in the main file
# (see System.repositories) so we can programatically download and
# extract them.
# This example requires Python 3.

import urllib.request
import zipfile
import tempfile
import shutil
import modelcif.reader


# Get any associated files containing pairwise QA scores
def _get_zip_scores_files(s):
    for repo in s.repositories:
        for f in repo.files:
            if isinstance(f, modelcif.associated.ZipFile):
                for zf in f.files:
                    if isinstance(
                            zf, modelcif.associated.LocalPairwiseQAScoresFile):
                        yield zf, f, repo


# Download entry ma-bak-cepc-0944 directly from ModelArchive
url = ("https://www.modelarchive.org/api/projects/"
       "ma-bak-cepc-0944?type=basic__model_file_name")
with urllib.request.urlopen(url) as fh:
    s, = modelcif.reader.read(fh)


# Get any referenced associated files containing QA scores. For ModelArchive,
# these are stored in an mmCIF file that is then compressed into a zip file
for scores, archive, repo in _get_zip_scores_files(s):
    url = repo.get_url(archive)
    # Download the referenced zip file directly from ModelArchive
    with urllib.request.urlopen(repo.get_url(archive)) as f_url:
        with tempfile.NamedTemporaryFile() as f_zip:
            shutil.copyfileobj(f_url, f_zip)
            # Extract the scores file from the zip file
            with zipfile.ZipFile(f_zip) as f_zip:
                with f_zip.open(scores.path) as f_scores:
                    # Add scores in the file to our existing System
                    modelcif.reader.read(f_scores, add_to_system=s)

for mg in s.model_groups:
    for m in mg:
        print("Model %s contains %d QA metrics" % (m, len(m.qa_metrics)))
