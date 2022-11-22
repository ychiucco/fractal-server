# This adapts clusterfutures <https://github.com/sampsyo/clusterfutures>
# Original Copyright
# Copyright 2021 Adrian Sampson <asampson@cs.washington.edu>
# License: MIT
#
# Copyright 2022 Jacopo Nepsolo <jacopo.nespolo@exact-lab.it>
import shlex
import subprocess  # nosec
import sys
from concurrent import futures
from pathlib import Path
from typing import Any
from typing import Callable
from typing import List
from typing import Optional

import cloudpickle
from cfut import RemoteException
from cfut import SlurmExecutor  # type: ignore
from cfut.util import random_string

from ....config import get_settings
from ....syringe import Inject
from ....utils import set_logger


def get_slurm_script_dir() -> Path:
    settings = Inject(get_settings)
    script_dir = settings.RUNNER_ROOT_DIR  # type: ignore
    return script_dir  # type: ignore


def get_stdout_filename(arg: str = "%j") -> Path:
    return get_slurm_script_dir() / f"slurmpy.stdout.{arg}.log"


def get_in_filename(arg) -> Path:
    return get_slurm_script_dir() / f"cfut.in.{arg}.pickle"


def get_out_filename(arg) -> Path:
    return get_slurm_script_dir() / f"cfut.out.{arg}.pickle"


def write_batch_script(
    sbatch_script: str, script_dir: Optional[Path] = None
) -> Path:
    """
    Write batch script

    Returns:
        batch_script_path:
            The path to the batch script
    """
    if not script_dir:
        script_dir = get_slurm_script_dir()

    batch_script_path = script_dir / f"_temp_{random_string()}.sh"
    with batch_script_path.open("w") as f:
        f.write(sbatch_script)
    return batch_script_path


def submit_sbatch(
    sbatch_script: str,
    submit_pre_command: str = "",
    script_dir: Optional[Path] = None,
) -> int:
    """
    Submit a Slurm job script

    Write the batch script in a temporary file and submit it with `sbatch`.

    Args:
        sbatch_script:
            the string representing the full job
        submit_pre_command:
            command that is prefixed to `sbatch`
        script_dir:
            destination of temporary script files

    Returns:
        jobid:
            integer job id as returned by `sbatch` submission
    """
    filename = write_batch_script(
        sbatch_script=sbatch_script, script_dir=script_dir
    )
    submit_command = f"sbatch --parsable {filename}"
    full_cmd = shlex.join(
        shlex.split(submit_pre_command) + shlex.split(submit_command)
    )
    try:
        output = subprocess.run(  # nosec
            full_cmd, capture_output=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logger = set_logger(logger_name="slurm_runner")
        logger.error(e.stderr)
        raise e
    jobid = output.stdout
    # NOTE after debugging this can be uncommented
    # filename.unlink()
    return int(jobid)


def compose_sbatch_script(
    cmdline: List[str],
    # NOTE: In SLURM, `%j` is the placeholder for the job_id.
    outpat: Optional[Path] = None,
    additional_setup_lines=[],
) -> str:
    if outpat is None:
        outpat = get_stdout_filename()
    script_lines = [
        "#!/bin/sh",
        f"#SBATCH --output={outpat}",
        *additional_setup_lines,
        # Export the slurm script directory so that nodes can find the pickled
        # payload
        f"export CFUT_DIR={get_slurm_script_dir()}",
        shlex.join(["srun", *cmdline]),
    ]
    return "\n".join(script_lines)


class FractalSlurmExecutor(SlurmExecutor):
    def __init__(
        self,
        username: Optional[str] = None,
        script_dir: Optional[Path] = None,
        *args,
        **kwargs,
    ):
        """
        Fractal slurm executor

        Args:
            username:
                shell username that runs the `sbatch` command
        """
        super().__init__(*args, **kwargs)
        self.username = username
        self.script_dir = script_dir

    def submit(
        self,
        fun: Callable[..., Any],
        *args,
        additional_setup_lines: List[str] = None,
        **kwargs,
    ):
        """Submit a job to the pool.
        If additional_setup_lines is passed, it overrides the lines given
        when creating the executor.
        """
        fut: futures.Future = futures.Future()

        # Start the job.
        workerid = random_string()
        funcser = cloudpickle.dumps((fun, args, kwargs))
        with get_in_filename(workerid).open("wb") as f:
            f.write(funcser)
        jobid = self._start(workerid, additional_setup_lines)

        if self.debug:
            print("job submitted: %i" % jobid, file=sys.stderr)

        # Thread will wait for it to finish.
        self.wait_thread.wait(get_out_filename(workerid).as_posix(), jobid)

        with self.jobs_lock:
            self.jobs[jobid] = (fut, workerid)
        return fut

    def _completion(self, jobid):
        """Called whenever a job finishes."""
        with self.jobs_lock:
            fut, workerid = self.jobs.pop(jobid)
            if not self.jobs:
                self.jobs_empty_cond.notify_all()
        if self.debug:
            print("job completed: %i" % jobid, file=sys.stderr)

        out_path = get_out_filename(workerid)
        in_path = get_in_filename(workerid)

        with out_path.open("rb") as f:
            outdata = f.read()
        success, result = cloudpickle.loads(outdata)

        if success:
            fut.set_result(result)
        else:
            fut.set_exception(RemoteException(result))

        # Clean up communication files.
        in_path.unlink()
        out_path.unlink()

        self._cleanup(jobid)

    def _start(self, workerid, additional_setup_lines):
        if additional_setup_lines is None:
            additional_setup_lines = self.additional_setup_lines

        settings = Inject(get_settings)
        python_worker_interpreter = (
            settings.SLURM_PYTHON_WORKER_INTERPRETER or sys.executable
        )

        sbatch_script = compose_sbatch_script(
            cmdline=shlex.split(
                f"{python_worker_interpreter} -m cfut.remote {workerid}"
            ),
            additional_setup_lines=additional_setup_lines,
        )

        pre_cmd = ""
        if self.username:
            pre_cmd = f"sudo --non-interactive -u {self.username}"

        job_id = submit_sbatch(
            sbatch_script,
            submit_pre_command=pre_cmd,
            script_dir=self.script_dir,
        )
        return job_id
