from pathlib import Path

from pydantic.decorator import validate_arguments

from .utils import _check_path_is_absolute


@validate_arguments
def cellpose_segmentation(
    *,
    path: str,
) -> None:
    """
    Dummy task description.
    """

    _check_path_is_absolute(path)
    print("[cellpose_segmentation] START")
    print(f"[cellpose_segmentation] {path=}")

    with (Path(path) / "data").open("a") as f:
        f.write("Cellpose segmentation\n")

    print("[cellpose_segmentation] END")
    return None
