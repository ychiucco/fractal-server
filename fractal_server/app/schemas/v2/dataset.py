from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import validator

from ....images import SingleImage
from ....images import val_scalar_dict
from .._validators import valstr
from .._validators import valutc
from ..v1.project import ProjectRead
from .dumps import WorkflowTaskDumpV2
from .workflowtask import WorkflowTaskStatusTypeV2


class _DatasetHistoryItemV2(BaseModel):
    """
    Class for an item of `Dataset.history`.
    """

    workflowtask: WorkflowTaskDumpV2
    status: WorkflowTaskStatusTypeV2
    parallelization: Optional[dict]


class DatasetStatusReadV2(BaseModel):
    """
    Response type for the
    `/project/{project_id}/dataset/{dataset_id}/status/` endpoint
    """

    status: Optional[
        dict[
            int,
            WorkflowTaskStatusTypeV2,
        ]
    ] = None


# CRUD


class DatasetCreateV2(BaseModel):

    name: str

    meta: dict[str, Any] = {}
    history: list[_DatasetHistoryItemV2] = []
    read_only: bool = False

    zarr_dir: str

    images: list[SingleImage] = []
    filters: dict[str, Any] = {}

    buffer: Optional[dict[str, Any]]
    parallelization_list: Optional[list[dict[str, Any]]]

    # Validators
    _name = validator("name", allow_reuse=True)(valstr("name"))
    _filters = validator("filters", allow_reuse=True)(
        val_scalar_dict("filters")
    )


class DatasetReadV2(BaseModel):

    id: int
    name: str

    project_id: int
    project: ProjectRead

    meta: dict[str, Any]
    history: list[_DatasetHistoryItemV2]
    read_only: bool

    timestamp_created: datetime

    zarr_dir: str

    images: list[SingleImage]
    filters: dict[str, Any]
    buffer: Optional[dict[str, Any]]
    parallelization_list: Optional[list[dict[str, Any]]]

    # Validators
    _timestamp_created = validator("timestamp_created", allow_reuse=True)(
        valutc("timestamp_created")
    )
    _filters = validator("filters", allow_reuse=True)(
        val_scalar_dict("filters")
    )


class DatasetUpdateV2(BaseModel):

    name: Optional[str]

    # Validators
    _name = validator("name", allow_reuse=True)(valstr("name"))
