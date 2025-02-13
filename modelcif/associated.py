"""Classes to associate extra files with the system.

   Typically, one or more :class:`Repository` objects are created and
   added to :attr:`modelcif.System.repositories`."""

import posixpath
import warnings


class Repository:
    """An online location where associated files can be found.
       These objects are typically added to
       :attr:`modelcif.System.repositories`.

       :param str url_root: URL root that prefixes each file's path.
              For example, if url_root is ``https://example.com`` then
              a :class:`File` with path ``test.txt`` can be found at
              ``https://example.com/test.txt``. If the files are not
              available online, None can be used here.
       :param list files: A list of :class:`File` objects.
    """
    def __init__(self, url_root, files):
        self.url_root = url_root
        self.files = files

    def get_url(self, f):
        """Get the full URL for the given :class:`File`"""
        return posixpath.join(self.url_root or '', f.path)


class File:
    """A single associated file. These objects can be added to a
       :class:`Repository` or a :class:`ZipFile`.

       :param str path: File name.
       :param str details: Any additional information about the file.
       :param data: If available, the data (e.g. sequence, structure,
              alignment) that are stored in the file.
       :type data: :class:`~modelcif.data.Data`
    """
    file_type = 'file'
    file_content = 'other'
    file_format = 'other'

    def __init__(self, path, details=None, data=None):
        self.path, self.details, self.data = path, details, data


class CIFFile(File):
    """An associated file in mmCIF or BinaryCIF format.
       See :class:`File` for more details.

       :param str path: File name that will be used to construct URLs in the
              main mmCIF file (see :class:`Repository` or :class:`ZipFile`).
       :param str details: Any additional information about the file.
       :param data: If available, the data (e.g. sequence, structure,
              alignment) that are stored in the file.
       :type data: :class:`~modelcif.data.Data`
       :param list categories: If given, any mmCIF category names in this list
              are written out to ``local_path`` by
              :func:`modelcif.dumper.write` instead of to the primary file
              handle.
       :param list copy_categories: If given, any mmCIF category names in this
              list are written out to both ``local_path`` by
              :func:`modelcif.dumper.write` and the primary file handle.
       :param str entry_id: Unique identifier for the associated file,
              if written (by specifying ``categories`` or ``copy_categories``).
       :param str entry_details: A comment to be added to the associated file,
              if written (by specifying ``categories`` or ``copy_categories``).
       :param str local_path: File name that will be used for ``categories``
              or ``copy_categories``. If not given, it defaults to the same
              as ``path``. (The file is always written directly to the local
              disk, even if this object is placed inside a :class:`ZipFile`.)
       :param bool binary: If False (the default), any output file is written
              in mmCIF format; if True, the file is written in BinaryCIF.
    """

    _binary_ff_map = {True: 'bcif', False: 'cif'}

    file_format = property(lambda self: self._binary_ff_map[self.binary],
                           doc="Format of the file (BinaryCIF or mmCIF)")

    def __init__(self, path, details=None, categories=[], copy_categories=[],
                 entry_id='model', entry_details=None, local_path=None,
                 binary=False, data=None):
        super(CIFFile, self).__init__(path, details, data)
        self.categories = categories
        self.copy_categories = copy_categories
        self.id = entry_id
        self.entry_details = entry_details
        self.local_path = local_path or path
        self.binary = binary


class QAMetricsFile(CIFFile):
    """An associated file in CIF format containing QA metrics.
       See :class:`CIFFile` for more details.
    """
    file_content = 'QA metrics'


# Map old class name to new equivalent
class LocalPairwiseQAScoresFile(QAMetricsFile):
    def __init__(self, *args, **keys):
        warnings.warn("LocalPairwiseQAScoresFile is deprecated. "
                      "Use QAMetricsFile instead.", stacklevel=2)
        super(LocalPairwiseQAScoresFile, self).__init__(*args, **keys)


class ZipFile(File):
    """An associated archive file in zip format, containing other files.
       See :class:`File` for more details.

       :param list files: A list of the :class:`File` objects contained
              within this archive. Note that an archive cannot contain another
              archive.
    """
    file_type = 'archive'
    file_content = 'archive with multiple files'
    file_format = 'zip'

    def __init__(self, path, details=None, files=[], data=None):
        super(ZipFile, self).__init__(path, details, data)
        self.files = files
