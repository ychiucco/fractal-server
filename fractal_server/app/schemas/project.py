from typing import Optional

from pydantic import BaseModel
from pydantic import validator

from ._validators import valstr
from .dataset import DatasetRead


__all__ = (
    "ProjectCreate",
    "ProjectRead",
    "ProjectUpdate",
)


class _ProjectBase(BaseModel):
    """
    Base class for `Project`.

    Attributes:
        name:
        read_only:
    """

    name: str
    read_only: bool = False


class ProjectCreate(_ProjectBase):
    """
    Class for `Project` creation.

    Attributes:
        default_dataset_name:
    """

    default_dataset_name: Optional[str] = "default"

    # Validators
    _name = validator("name", allow_reuse=True)(valstr("name"))
    _default_dataset_name = validator(
        "default_dataset_name", allow_reuse=True
    )(valstr("default_dataset_name"))


class ProjectRead(_ProjectBase):
    """
    Class for `Project` read from database.

    Attributes:
        id:
        dataset_list:
    """

    id: int
    dataset_list: list[DatasetRead] = []


class ProjectUpdate(_ProjectBase):
    """
    Class for `Project` update.

    Attributes:
        name:
        read_only:
    """

    name: Optional[str]
    read_only: Optional[bool]

    # Validators
    _name = validator("name", allow_reuse=True)(valstr("name"))