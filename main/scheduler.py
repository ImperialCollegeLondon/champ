import os
import subprocess
import sys
from pathlib import Path

from .portal_config import get_portal_settings

SCRIPT_DIR = Path(__file__).absolute().parent / "ruby_scripts"


class SchedulerError(Exception):
    pass


def submit(script_path, submission_dir, timeout=10):
    """Submit a job to the scheduler.

    args:
      script_path (str or Path): path to the submission script
      submission_dir (Path): location to submit script from
      timeout (int): Number of seconds to wait before giving up

    returns:
      (str): The returned job id
    """
    return run_ruby_script(
        "submit.rb", [script_path], timeout=timeout, run_dir=submission_dir
    )


def status(job_id, timeout=2):
    """Return the status of a job.

    args:
      job_id (str): id of the job to query
      timeout (int): Number of seconds to wait before giving up

    returns:
      (str): The job status. One of "Queueing", "Running" or "Completed".
    """
    return run_ruby_script("status.rb", [job_id], timeout=timeout)


def delete(job_id, timeout=10):
    """Delete a job from the scheduler.

    args:
      job_id (str): id of the job to query
      timeout (int): Number of seconds to wait before giving up

    returns:
      (str): Standard output from the deletion
    """
    return run_ruby_script("delete.rb", [job_id], timeout=timeout)


def run_ruby_script(script_name, cmdline_args, timeout, run_dir=None):
    """Run a ruby script as a subprocess. If the process fails or does not complete
    within `timeout` seconds a SchedulerError is raised.

    args:
      script_name (str): file name of the ruby script to run
      cmdline_args (list): the command line arguments to pass to the script
      timeout (int): number of seconds to wait for command to run
      run_dir (Path): the working directory for the subprocess

    returns:
      (str): stdout from the executed script
    """

    run_dir = run_dir if run_dir else os.getenv("HOME", "/tmp")

    command = (
        ["ruby", str(SCRIPT_DIR / script_name)]
        + cmdline_args
        + [get_portal_settings().CLUSTER]
    )
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
        raise SchedulerError(e.stderr.decode(sys.getfilesystemencoding()).strip())
    except subprocess.TimeoutExpired:
        raise SchedulerError("Scheduler command timed out")

    return cp.stdout.decode(sys.getfilesystemencoding()).strip()
