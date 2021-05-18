import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).absolute().parent / "ruby_scripts"


def submit(script_path, submission_dir):
    return run_ruby_script("submit.rb", [script_path], submission_dir)


def status(job_id):
    return run_ruby_script("status.rb", [job_id])


def delete(job_id):
    return run_ruby_script("delete.rb", [job_id])


def run_ruby_script(script_name, cmdline_args, run_dir=None):
    """Executes `script_name` from SCRIPT_DIR with `args` in `run_dir` in
    an external process and returns stdout if successful, otherwise
    raises subprocess.SubprocessError containing stderr.

    """

    run_dir = run_dir if run_dir else os.getenv("HOME", "/tmp")

    command = ["ruby", str(SCRIPT_DIR / script_name)] + cmdline_args
    cp = subprocess.run(  # blocking call
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=run_dir,
    )
    return cp.stdout.decode(sys.getfilesystemencoding()).strip()
