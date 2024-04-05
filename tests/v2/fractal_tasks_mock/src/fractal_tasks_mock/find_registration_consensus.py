from pathlib import Path

from fractal_tasks_mock.utils import _group_paths_by_well
from pydantic.decorator import validate_arguments


@validate_arguments
def find_registration_consensus(
    *,
    paths: list[str],
    zarr_dir: str,
) -> None:
    """
    Dummy task description.

    Arguments:
        paths: description
        zarr_dir: description
    """

    print("[find_registration_consensus] START")
    well_to_paths = _group_paths_by_well(paths)
    for well, well_paths in well_to_paths.items():
        print(f"[find_registration_consensus] {well=}")
        for path in well_paths:

            table_path = Path(path) / "registration_table"
            try:
                with table_path.open("r") as f:
                    f.read()
                print(
                    f"[find_registration_consensus]  "
                    f"Read {table_path.as_posix()}"
                )
            except FileNotFoundError:
                print(
                    f"[find_registration_consensus]  "
                    f"FAIL Reading {table_path.as_posix()}"
                )

        print(f"[find_registration_consensus] Find consensus for {well=}")
        for path in well_paths:
            table_path = Path(path) / "registration_table_final"
            print(
                "[find_registration_consensus]"
                f"   Write {table_path.as_posix()}"
            )
            with table_path.open("w") as f:
                f.write("This is the consensus-based new table.\n")

    print("[find_registration_consensus] END")


if __name__ == "__main__":
    from utils import run_fractal_task

    run_fractal_task(task_function=find_registration_consensus)