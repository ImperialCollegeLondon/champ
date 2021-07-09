"""Implementation of a generator that creates a zip archive on the fly
from file input and yields bytestrings of the archive
content. Designed to be used in conjunction with a
StreamingHttpResponse for synchronous download of zip archives without
the need to write a temporary file to disk.

Based on https://stackoverflow.com/a/55169752

The major drawback of this approach is that the Django worker thread
is tied up with writing the archive and the rest of the site is
unresponsive. Due to the use of PUN servers by OOD this only affects a
single user however so is mitigated through UI design.

"""

from io import RawIOBase
from pathlib import Path
from zipfile import ZipFile, ZipInfo

CHUNK_SIZE_BYTES = 16 * 1024


class Stream(RawIOBase):
    """A simple stream object used to store zip archive chunks in memory
    before being included in a response."""

    def __init__(self):
        self._buffer = b""

    def writable(self):
        return True

    def write(self, b):
        if self.closed:
            raise ValueError("Stream was closed!")
        self._buffer += b
        return len(b)

    def get(self):
        chunk = self._buffer
        self._buffer = b""
        return chunk


def zipfile_generator(dir_name, paths):
    """Generator yielding bytestrings for a zip archive constructed on the
    fly. The zip archive will contain the files specified by `paths`
    (iterable of pathlib.Path) in a parent directory `dir_name` (str).
    """
    stream = Stream()
    with ZipFile(stream, mode="w") as zf:
        for path in paths:
            z_info = ZipInfo.from_file(path, arcname=Path(dir_name, path.name))
            with open(path, "rb") as entry, zf.open(z_info, mode="w") as dest:
                for chunk in iter(lambda: entry.read(CHUNK_SIZE_BYTES), b""):
                    dest.write(chunk)
                    yield stream.get()
    # ZipFile was closed.
    yield stream.get()
