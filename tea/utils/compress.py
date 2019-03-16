__author__ = "Viktor Kerkez <alefnula@gmail.com>"
__date__ = "07 January 2009"
__copyright__ = "Copyright (c) 2009 Viktor Kerkez"

import os
import zipfile
import logging
from tea import shell
from tea.system import platform
from tea.process import execute_and_report as er

logger = logging.getLogger(__name__)


def _extract_file(archive, destination, filename):
    try:
        output_path = os.path.join(destination, filename)
        output_dir = os.path.dirname(output_path)
        if not os.path.isdir(output_dir):
            shell.mkdir(output_dir)
        # Cannot write big chunks of data to windows shares
        MAX_BYTES = 5242880  # 5MB
        reader = archive.open(filename)
        writer = open(output_path, "wb")
        while True:
            data = reader.read(MAX_BYTES)
            if len(data) > 0:
                writer.write(data)
            else:
                break
        return True
    except Exception:
        logger.exception(
            "Error while unzipping filename %s from archive %s"
            % (filename, archive.filename)
        )
        return False


def unzip(archive, destination, filenames=None):
    """Unzip a zip archive into destination directory.

    It unzips either the whole archive or specific file(s) from the archive.

    Usage:
        >>> output = os.path.join(os.getcwd(), 'output')
        >>> # Archive can be an instance of a ZipFile class
        >>> archive = zipfile.ZipFile('test.zip', 'r')
        >>> # Or just a filename
        >>> archive = 'test.zip'
        >>> # Extracts all files
        >>> unzip(archive, output)
        >>> # Extract only one file
        >>> unzip(archive, output, 'my_file.txt')
        >>> # Extract a list of files
        >>> unzip(archive, output, ['my_file1.txt', 'my_file2.txt'])
        >>> unzip_file('test.zip', 'my_file.txt', output)

    Args:
        archive (zipfile.ZipFile or str): Zipfile object to extract from or
            path to the zip archive.
        destination (str): Path to the output directory.
        filenames (str or list of str or None): Path(s) to the filename(s)
            inside the zip archive that you want to extract.
    """
    close = False
    try:
        if not isinstance(archive, zipfile.ZipFile):
            archive = zipfile.ZipFile(archive, "r", allowZip64=True)
            close = True
        logger.info("Extracting: %s -> %s" % (archive.filename, destination))
        if isinstance(filenames, str):
            filenames = [filenames]
        if filenames is None:  # extract all
            filenames = archive.namelist()
        for filename in filenames:
            if filename.endswith("/"):  # it's a directory
                shell.mkdir(os.path.join(destination, filename))
            else:
                if not _extract_file(archive, destination, filename):
                    raise Exception()
        logger.info('Extracting zip archive "%s" succeeded' % archive.filename)
        return True
    except Exception:
        logger.exception("Error while unzipping archive %s" % archive.filename)
        return False
    finally:
        if close:
            archive.close()


def mkzip(archive, items, mode="w", save_full_paths=False):
    """Recursively zip a directory.

    Args:
        archive (zipfile.ZipFile or str): ZipFile object add to or path to the
            output zip archive.
        items (str or list of str): Single item or list of items (files and
            directories) to be added to zipfile.
        mode (str): w for create new and write a for append to.
        save_full_paths (bool): Preserve full paths.
    """
    close = False
    try:
        if not isinstance(archive, zipfile.ZipFile):
            archive = zipfile.ZipFile(archive, mode, allowZip64=True)
            close = True
        logger.info("mkdzip: Creating %s, from: %s", archive.filename, items)
        if isinstance(items, str):
            items = [items]
        for item in items:
            item = os.path.abspath(item)
            basename = os.path.basename(item)
            if os.path.isdir(item):
                for root, directoires, filenames in os.walk(item):
                    for filename in filenames:
                        path = os.path.join(root, filename)
                        if save_full_paths:
                            archive_path = path.encode("utf-8")
                        else:
                            archive_path = os.path.join(
                                basename, path.replace(item, "").strip("\\/")
                            ).encode("utf-8")
                        archive.write(path, archive_path)
            elif os.path.isfile(item):
                if save_full_paths:
                    archive_name = item.encode("utf-8")
                else:
                    archive_name = basename.encode("utf-8")
                archive.write(item, archive_name)  # , zipfile.ZIP_DEFLATED)
        return True
    except Exception as e:
        logger.error("Error occurred during mkzip: %s" % e)
        return False
    finally:
        if close:
            archive.close()


_SZ_EXECUTABLE = None


def _get_sz():
    global _SZ_EXECUTABLE
    if _SZ_EXECUTABLE is None:
        _SZ_EXECUTABLE = "7z"
        if platform.is_a(platform.WINDOWS):
            for pf in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
                executable = os.path.join(
                    os.environ.get(pf, ""), "7-Zip", "7z.exe"
                )
                if os.path.exists(executable):
                    _SZ_EXECUTABLE = executable
                    break
    return _SZ_EXECUTABLE


def seven_zip(archive, items, self_extracting=False):
    """Create a 7z archive."""
    if not isinstance(items, (list, tuple)):
        items = [items]
    if self_extracting:
        return er(_get_sz(), "a", "-ssw", "-sfx", archive, *items)
    else:
        return er(_get_sz(), "a", "-ssw", archive, *items)


def seven_unzip(archive, output):
    """Extract a 7z archive."""
    return er(_get_sz(), "x", archive, "-o%s" % output, "-aoa")
