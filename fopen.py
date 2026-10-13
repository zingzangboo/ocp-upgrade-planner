"""
fopen.py"
"""

import locale

def fopen(
        filename,
        mode='r',
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None
):
    """
    Open a file, without triggering pylint W1514 "unspecified-encoding",
    and without requiring the developer to choose some particular encoding.

    The pylint check appears to be intended for code that reads a file encoded
    in some particular encoding, and which is intended to run on many
    different operating systems, whose native encodings may differ from the
    encoding used in the file.

    In this case, it is important to explicitly tell Python to read the file
    using the encoding that the file is actually encoded using, else Python
    will use a default encoding, which may not match the file's encoding,
    which may therefore cause corruption of the file's data.

    For example, Linux software usually uses UTF-8 in on-disk files, whereas
    Windows NT and its successors have used UCS-2LE and UTF-16LE at different
    times in the past, and are now transitioning to use of UTF-8.

    Reading a text file of a certain known encoding is an important use case,
    but it is not the sole way that a correct Python program might want to
    read (or write) a text file.
    Sometimes, a file is only ever read on the same operating system that it
    was written on, by the same Python code, so there are no portability
    concerns. Instead, the operating system merely needs to be
    self-consistent across read and write encodings.

    In this case, it is better to use the operating system's preferred
    encoding than to hard-code some encoding, then blindly hope that that
    encoding a) works and b) is efficient on every single one of the
    many operating systems that Python runs on.

    There is no way that pylint can know which of these two mutually exclusive
    cases pertains (or some other case), so its warning cannot always be
    correct, so it will sometimes be wrong, so it must be defeated always.

    Rather than force the developer to copy'n'paste the below workaround
    all through their code, it is centralised here.

    The developer may still pass an encoding, if they want or need to, for
    example if they are in the specific scenario described above.

    For the (seemingly misguided) rationale behind the pylint check, and the
    workaround used below, see:
    https://peps.python.org/pep-0597/
    """
    if encoding is None:
        encoding = locale.getpreferredencoding(False)
    return open(
        filename, mode, buffering, encoding, errors, newline, closefd, opener
    )
