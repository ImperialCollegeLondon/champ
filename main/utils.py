import os
from datetime import datetime

import humanize


def file_properties(path):
    """Return the name, modification time and size of a file.

    args:
      path (str or Path): path to file of interest

    returns:
      (dict): file properties with keys "name", "mtime" and "file_size"
    """
    stats = os.stat(path)
    return dict(
        name=path.name,
        mtime=humanize.naturaltime(datetime.fromtimestamp(stats.st_mtime)),
        file_size=humanize.naturalsize(stats.st_size),
    )
