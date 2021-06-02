import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).absolute().parent / "ruby_scripts"


class SchedulerError(Exception):
    pass


def submit(script_path, submission_dir, timeout=10):
    return run_ruby_script(
        "submit.rb", [script_path], timeout=timeout, run_dir=submission_dir
    )


def status(job_id, timeout=2):
    return run_ruby_script("status.rb", [job_id], timeout=timeout)


def delete(job_id, timeout=10):
    return run_ruby_script("delete.rb", [job_id], timeout=timeout)


def run_ruby_script(script_name, cmdline_args, timeout, run_dir=None):
    """Executes `script_name` from SCRIPT_DIR with `args` in `run_dir` in
    an external process and returns stdout if successful. If the
    process fails or does not complete within `timeout` seconds a
    SchedulerError is raised.
    """

    run_dir = run_dir if run_dir else os.getenv("HOME", "/tmp")

    command = ["ruby", str(SCRIPT_DIR / script_name)] + cmdline_args
    try:
        cp = subprocess.run(  # blocking call
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=run_dir,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        raise SchedulerError(e.stderr)
    except subprocess.TimeoutExpired:
        raise SchedulerError("Scheduler command timed out")

    return cp.stdout.decode(sys.getfilesystemencoding()).strip()
