import os
import shlex
import signal
import subprocess
import time
from pathlib import Path

import pytest
from devtools import debug

import fractal_server
from tests.fixtures_server import DB_ENGINE


FRACTAL_SERVER_DIR = Path(fractal_server.__file__).parent


@pytest.fixture(scope="function")
async def set_test_db(tmp_path):

    if not tmp_path.exists():
        tmp_path.mkdir(parents=True)

    cwd = str(tmp_path)

    # General config
    config_lines = [
        f"DB_ENGINE={DB_ENGINE}",
        f"FRACTAL_TASKS_DIR={cwd}/FRACTAL_TASKS_DIR",
        f"FRACTAL_RUNNER_WORKING_BASE_DIR={cwd}/artifacts",
        "JWT_SECRET_KEY=secret",
        "FRACTAL_LOGGING_LEVEL=10",
    ]

    # DB_ENGINE-specific config
    if DB_ENGINE == "postgres":
        config_lines.extend(
            [
                "POSTGRES_USER=postgres",
                "POSTGRES_PASSWORD=postgres",
                "POSTGRES_DB=fractal_test",
            ]
        )
    elif DB_ENGINE == "sqlite":
        if "SQLITE_PATH" in os.environ:
            SQLITE_PATH = os.environ.pop("SQLITE_PATH")
            debug(f"Dropped {SQLITE_PATH=} from `os.environ`.")
        config_lines.append(f"SQLITE_PATH={cwd}/test.db")
        debug(f"SQLITE_PATH={cwd}/test.db")
    else:
        raise ValueError(f"Invalid {DB_ENGINE=}")

    # Write config to file
    config = "\n".join(config_lines + ["\n"])
    with (FRACTAL_SERVER_DIR / ".fractal_server.env").open("w") as f:
        f.write(config)

    # Initialize db
    cmd = "poetry run fractalctl set-db"
    debug(cmd)
    res = subprocess.run(
        shlex.split(cmd),
        encoding="utf-8",
        capture_output=True,
        cwd=FRACTAL_SERVER_DIR,
    )
    debug(res.stdout)
    debug(res.stderr)
    debug(res.returncode)
    assert res.returncode == 0

    yield

    if DB_ENGINE == "postgres":
        # Apply migrations on reverse until database is dropped, in order to
        # keep tests stateless:
        # https://alembic.sqlalchemy.org/en/latest/tutorial.html#downgrading
        # Not required by SQLite. In that case we do not remove the `test.db`
        # file, which can be read after the test.
        cmd = "poetry run alembic downgrade base"
        res = subprocess.run(
            shlex.split(cmd),
            encoding="utf-8",
            capture_output=True,
            cwd=FRACTAL_SERVER_DIR,
        )
        debug(res.stdout)
        debug(res.stderr)
        debug(res.returncode)
        assert res.returncode == 0
    # Removing env file (to keep tests stateless)
    Path.unlink(FRACTAL_SERVER_DIR / ".fractal_server.env")


def test_set_db(tmp_path: Path, set_test_db):
    """
    Run `poetry run fractalctl set-db`
    """
    debug(DB_ENGINE)
    if DB_ENGINE == "sqlite":
        db_file = str(tmp_path / "test.db")
        debug(db_file)
        assert os.path.exists(db_file)


def test_alembic_check(set_test_db):
    """
    Run `poetry run alembic check` to see whether new migrations are needed
    """

    # Run check
    cmd = "poetry run alembic check"

    debug(cmd)
    res = subprocess.run(
        shlex.split(cmd),
        encoding="utf-8",
        capture_output=True,
        cwd=FRACTAL_SERVER_DIR,
    )
    debug(res.stdout)
    debug(res.stderr)
    if not res.returncode == 0:
        raise ValueError(
            f"Command `{cmd}` failed with exit code {res.returncode}.\n"
            f"Original stdout: {res.stdout}\n"
            f"Original stderr: {res.stderr}\n"
        )
    assert "No new upgrade operations detected" in res.stdout


commands = [
    "fractalctl start",
    "fractalctl start --reload --host 0.0.0.0 --port 8000",
    "gunicorn fractal_server.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4",  # noqa
]


@pytest.mark.parametrize("cmd", commands)
def test_startup_commands(cmd, set_test_db):

    debug(cmd)
    p = subprocess.Popen(
        shlex.split(f"poetry run {cmd}"),
        start_new_session=True,
        cwd=FRACTAL_SERVER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    debug(p)
    with pytest.raises(subprocess.TimeoutExpired) as e:
        p.wait(timeout=1.5)
        out, err = p.communicate()
        debug(p.returncode)
        debug(out)
        debug(err)
        assert p.returncode == 0

    debug("Now call killpg")
    debug(p)
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    # Wait a bit, so that the killpg ends before pytest ends
    time.sleep(0.3)
    debug(e.value)
