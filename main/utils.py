import os
from datetime import datetime

import humanize


def file_properties(path):
    stats = os.stat(path)
    return dict(
        name=path.name,
        mtime=humanize.naturaltime(datetime.fromtimestamp(stats.st_mtime)),
        file_size=humanize.naturalsize(stats.st_size),
    )
