from enum import Enum
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from .._validators import valint
from ..v1.task import TaskExport
from ..v1.task import TaskImport
from ..v1.task import TaskRead
from .task import TaskExportV2
from .task import TaskImportV2
from .task import TaskReadV2
from fractal_server.images import Filters


class WorkflowTaskStatusTypeV2(str, Enum):
    """
    Define the available values for the status of a `WorkflowTask`.

    This model is used within the `Dataset.history` attribute, which is
    constructed in the runner and then used in the API (e.g. in the
    `api/v2/project/{project_id}/dataset/{dataset_id}/status` endpoint).

    Attributes:
        SUBMITTED: The `WorkflowTask` is part of a running job.
        DONE: The most-recent execution of this `WorkflowTask` was successful.
        FAILED: The most-recent execution of this `WorkflowTask` failed.
    """

    SUBMITTED = "submitted"
    DONE = "done"
    FAILED = "failed"


class WorkflowTaskCreateV2(BaseModel):

    meta: Optional[dict[str, Any]]
    args: Optional[dict[str, Any]]
    order: Optional[int]
    input_filters: Filters = Field(default_factory=Filters)

    is_legacy_task: bool = False

    # Validators

    _order = validator("order", allow_reuse=True)(valint("order", min_val=0))


class WorkflowTaskReadV2(BaseModel):

    id: int

    workflow_id: int
    order: Optional[int]
    meta: Optional[dict[str, Any]]
    args: Optional[dict[str, Any]]

    input_filters: Filters

    is_legacy_task: bool
    task_id: Optional[int]
    task: Optional[TaskReadV2]
    task_legacy_id: Optional[int]
    task_legacy: Optional[TaskRead]


class WorkflowTaskUpdateV2(BaseModel):

    meta: Optional[dict[str, Any]]
    args: Optional[dict[str, Any]]
    input_filters: Optional[Filters]

    # Validators

    @validator("meta")
    def check_no_parallelisation_level(cls, m):
        if "parallelization_level" in m:
            raise ValueError(
                "Overriding task parallelization level currently not allowed"
            )
        return m


class WorkflowTaskImportV2(BaseModel):

    meta: Optional[dict[str, Any]] = None
    args: Optional[dict[str, Any]] = None

    input_filters: Optional[Filters] = None

    is_legacy_task: bool = False
    task: Optional[TaskImportV2] = None
    task_legacy: Optional[TaskImport] = None


class WorkflowTaskExportV2(BaseModel):

    meta: Optional[dict[str, Any]] = None
    args: Optional[dict[str, Any]] = None
    input_filters: Filters = Field(default_factory=Filters)

    is_legacy_task: bool = False
    task: Optional[TaskExportV2]
    task_legacy: Optional[TaskExport]
