import shlex
import subprocess
import time

import pytest
from devtools import debug

from fractal_server.app.runner.exceptions import JobExecutionError
from fractal_server.app.runner.executors.slurm.executor import (
    FractalSlurmExecutor,
)
from tests.fixtures_slurm import run_squeue


def test_direct_shutdown_during_submit(
    monkey_slurm,
    monkey_slurm_user,
    tmp777_path,
):
    """
    Test the FractalSlurmExecutor.shutdown method directly
    """

    executor = FractalSlurmExecutor(
        slurm_user=monkey_slurm_user,
        working_dir=tmp777_path,
        working_dir_user=tmp777_path,
        slurm_poll_interval=2,
        keep_pickle_files=True,
    )

    # NOTE: this function has to be defined inside the test function, so that
    # this works correctly with cloudpickle. In principle one could make it
    # work with cloudpickle as well, via register_pickle_by_value (see
    # https://github.com/fractal-analytics-platform/fractal-server/issues/690)
    # but we observed some unexpected behavior and did not investigate further.
    # Note that this only affects the CI, while the function to be executed via
    # FractalSlurmExecutor in fractal-server are always imported from a kwown
    # package (i.e. fractal-server itself).
    def _sleep_and_return(sleep_time):
        time.sleep(sleep_time)
        return 42

    res = executor.submit(_sleep_and_return, 100)
    debug(res)
    debug(run_squeue())
    executor.shutdown()
    executor.wait_thread.shutdown = True
    debug(res)
    assert not run_squeue(header=False)

    try:
        _ = res.result()
    except JobExecutionError as e:
        debug(e)
    except Exception as e:
        debug(e)
        raise e


def test_indirect_shutdown_during_submit(
    monkey_slurm,
    monkey_slurm_user,
    tmp777_path,
    tmp_path,
):
    """
    Test the FractalSlurmExecutor.shutdown method indirectly, that is, when it
    is triggered by the presence of a shutdown_file
    """
    shutdown_file = tmp_path / "shutdown"

    executor = FractalSlurmExecutor(
        slurm_user=monkey_slurm_user,
        working_dir=tmp777_path,
        working_dir_user=tmp777_path,
        slurm_poll_interval=1,
        keep_pickle_files=True,
        shutdown_file=str(shutdown_file),
    )

    # NOTE: this has to be defined here, see note above and
    # https://github.com/fractal-analytics-platform/fractal-server/issues/690
    def _sleep_and_return(sleep_time):
        time.sleep(sleep_time)
        return 42

    res = executor.submit(_sleep_and_return, 100)
    debug(res)
    debug(run_squeue())

    with shutdown_file.open("w") as f:
        f.write("")
    assert shutdown_file.exists()
    time.sleep(2)

    debug(executor.wait_thread.shutdown)
    assert executor.wait_thread.shutdown

    time.sleep(4)

    debug(res)
    debug(run_squeue())

    assert not run_squeue(header=False)
    try:
        _ = res.result()
    except JobExecutionError as e:
        debug(e)
    except Exception as e:
        debug(e)
        raise e


def test_indirect_shutdown_during_map(
    monkey_slurm,
    monkey_slurm_user,
    tmp777_path,
    tmp_path,
):
    def fun_sleep(dummy):
        time.sleep(100)
        return 42

    shutdown_file = tmp_path / "shutdown"

    # NOTE: the executor.map call below is blocking. For this reason, we write
    # the shutdown file from a subprocess.Popen, so that we can make it happen
    # during the execution.
    shutdown_sleep_time = 2
    tmp_script = (tmp_path / "script.sh").as_posix()
    debug(tmp_script)
    with open(tmp_script, "w") as f:
        f.write(f"sleep {shutdown_sleep_time}\n")
        f.write(f"cat NOTHING > {shutdown_file.as_posix()}\n")

    tmp_stdout = open((tmp_path / "stdout").as_posix(), "w")
    tmp_stderr = open((tmp_path / "stderr").as_posix(), "w")
    subprocess.Popen(
        shlex.split(f"bash {tmp_script}"),
        stdout=tmp_stdout,
        stderr=tmp_stderr,
    )

    with FractalSlurmExecutor(
        slurm_user=monkey_slurm_user,
        working_dir=tmp777_path,
        working_dir_user=tmp777_path,
        slurm_poll_interval=2,
        keep_pickle_files=True,
        shutdown_file=str(shutdown_file),
    ) as executor:

        res = executor.map(fun_sleep, range(25))
        debug(run_squeue())

        time.sleep(shutdown_sleep_time + 1)
        debug(run_squeue())

        with pytest.raises(JobExecutionError) as e:
            list(res)
        debug(e.value)
        assert "shutdown" in str(e.value)

    tmp_stdout.close()
    tmp_stderr.close()
