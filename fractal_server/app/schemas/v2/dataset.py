from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from .._validators import valstr
from .._validators import valutc
from ..v1.project import ProjectRead
from .dumps import WorkflowTaskDumpV2
from .workflowtask import WorkflowTaskStatusTypeV2
from fractal_server.app.runner.v2.filters import Filters


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

    read_only: bool = False
    zarr_dir: str

    filters: Filters = Field(default_factory=Filters)

    # Validators
    _name = validator("name", allow_reuse=True)(valstr("name"))


class DatasetReadV2(BaseModel):

    id: int
    name: str

    project_id: int
    project: ProjectRead

    history: list[_DatasetHistoryItemV2]
    read_only: bool

    timestamp_created: datetime

    zarr_dir: str
    filters: Filters = Field(default_factory=Filters)

    # Validators
    _timestamp_created = validator("timestamp_created", allow_reuse=True)(
        valutc("timestamp_created")
    )


class DatasetUpdateV2(BaseModel):
    class Config:
        extra = "forbid"

    name: Optional[str]
    read_only: Optional[bool]
    zarr_dir: Optional[str]
    filters: Optional[Filters]

    # Validators
    _name = validator("name", allow_reuse=True)(valstr("name"))
