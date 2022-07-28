"""Classes to associate extra files with the system.

   Typically, one or more :class:`Repository` objects are created and
   added to :attr:`modelcif.System.repositories`."""

import posixpath


class Repository(object):
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


class File(object):
    """A single associated file. These objects can be added to a
       :class:`Repository` or a :class:`ZipFile`.

       :param str path: File name.
       :param str details: Any additional information about the file.
    """
    file_type = 'file'
    file_content = 'other'
    file_format = 'other'

    def __init__(self, path, details=None):
        self.path, self.details = path, details


class CIFFile(File):
    """An associated file in mmCIF or BinaryCIF format.
       See :class:`File` for more details.

       :param str path: File name that will be used to construct URLs in the
              main mmCIF file (see :class:`Repository` or :class:`ZipFile`).
       :param str details: Any additional information about the file.
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

    file_format = property(lambda self: self._binary_ff_map[self.binary])

    def __init__(self, path, details=None, categories=[], copy_categories=[],
                 entry_id='model', entry_details=None, local_path=None,
                 binary=False):
        super(CIFFile, self).__init__(path, details)
        self.categories = categories
        self.copy_categories = copy_categories
        self.id = entry_id
        self.entry_details = entry_details
        self.local_path = local_path or path
        self.binary = binary


class LocalPairwiseQAScoresFile(CIFFile):
    """An associated file in CIF format containing local pairwise QA scores.
       See :class:`CIFFile` for more details.
    """
    file_content = 'local pairwise QA scores'


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

    def __init__(self, path, details=None, files=[]):
        super(ZipFile, self).__init__(path, details)
        self.files = files
