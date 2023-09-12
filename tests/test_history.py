import json
import logging

from devtools import debug

from fractal_server.app.runner._common import METADATA_FILENAME
from fractal_server.app.runner.history import (
    assemble_history_failed_job,
)  # noqa


async def test_get_workflowtask_status(
    db,
    MockCurrentUser,
    tmp_path,
    project_factory,
    task_factory,
    dataset_factory,
    workflow_factory,
    job_factory,
    client,
):
    """
    This test reflects the behavior of
    `/project/{project_id}/dataset/{dataset_id}/status/` which gives different
    priority to different sources. From lowest to highest priority:

    * Statuses already present in `output_dataset.meta["history"]`, in the
        database;
    * "submitted" status for all task in the current job;
    * Temporary-file contents.
    """

    RESULTS = dict(done=set(), failed=set(), submitted=set())

    # (A) These statuses will be written in the metadata file, and they will be
    # the final ones - as there exist no corresponding WorkflowTasks
    history = []
    for shift, status in enumerate(["done", "failed"]):
        ID = 100 + shift
        history.append(dict(workflowtask=dict(id=ID), status=status))
        RESULTS[status].add(ID)

    working_dir = tmp_path / "working_dir"
    working_dir.mkdir()
    with (working_dir / METADATA_FILENAME).open("w") as f:
        tmp_meta = dict(history=history)
        json.dump(tmp_meta, f)
    debug(working_dir / METADATA_FILENAME)

    async with MockCurrentUser(persist=True) as user:
        project = await project_factory(user)
        task = await task_factory(name="task1", source="task1")
        workflow = await workflow_factory(project_id=project.id, name="WF")
        input_dataset = await dataset_factory(project_id=project.id)

        # Prepare output_dataset.meta["history"]
        history = []

        # (B) The statuses for these IDs will be overwritten by "submitted",
        # because they match with the task_list of the workflow associated to a
        # job associated to output_dataset
        for dummy_status in ["done", "failed", "submitted"]:
            await workflow.insert_task(task_id=task.id, db=db)
            ID = workflow.task_list[-1].id
            history.append(dict(workflowtask=dict(id=ID), status=dummy_status))
            RESULTS["submitted"].add(ID)
        await db.close()

        # (C) The statuses for these IDs will be the final ones, as there are
        # no corresponding WorkflowTasks
        for shift, status in enumerate(["done", "failed", "submitted"]):
            ID = 200 + shift
            history.append(dict(workflowtask=dict(id=ID), status=status))
            RESULTS[status].add(ID)

        # Create output_dataset and job
        meta = dict(history=history)
        output_dataset = await dataset_factory(
            project_id=project.id, meta=meta
        )
        job = await job_factory(  # noqa
            project_id=project.id,
            workflow_id=workflow.id,
            input_dataset_id=input_dataset.id,
            output_dataset_id=output_dataset.id,
            working_dir=str(working_dir),
        )

        # Test get_workflowtask_status endpoint
        res = await client.get(
            f"api/v1/project/{project.id}/dataset/{output_dataset.id}/status/"
        )
        debug(res.status_code)
        assert res.status_code == 200
        statuses = res.json()["status"]
        debug(statuses)
        for expected_status, IDs in RESULTS.items():
            for ID in IDs:
                ID_str = str(ID)  # JSON-object keys can only be strings
                assert statuses[ID_str] == expected_status


async def test_get_workflowtask_status_simple(
    db,
    MockCurrentUser,
    tmp_path,
    project_factory,
    task_factory,
    dataset_factory,
    workflow_factory,
    job_factory,
    client,
):
    """
    Same as test_get_workflowtask_status, but without any temporary metadata
    file in `working_dir`.
    """

    RESULTS = dict(done=set(), failed=set(), submitted=set())
    working_dir = tmp_path / "working_dir"

    async with MockCurrentUser(persist=True) as user:
        project = await project_factory(user)
        task = await task_factory(name="task1", source="task1")
        workflow = await workflow_factory(project_id=project.id, name="WF")
        input_dataset = await dataset_factory(project_id=project.id)

        # (B) The statuses for these IDs will be overwritten by "submitted",
        # because they match with the task_list of the workflow associated to a
        # job associated to output_dataset
        history = []
        for dummy_status in ["done", "failed", "submitted"]:
            await workflow.insert_task(task_id=task.id, db=db)
            ID = workflow.task_list[-1].id
            history.append(dict(workflowtask=dict(id=ID), status=dummy_status))
            RESULTS["submitted"].add(ID)
        await db.close()

        # (C) The statuses for these IDs will be the final ones, as there are
        # no corresponding WorkflowTasks
        for shift, status in enumerate(["done", "failed", "submitted"]):
            ID = 200 + shift
            history.append(dict(workflowtask=dict(id=ID), status=status))
            RESULTS[status].add(ID)

        # Create output_dataset and job
        meta = dict(history=history)
        output_dataset = await dataset_factory(
            project_id=project.id, meta=meta
        )
        job = await job_factory(  # noqa
            project_id=project.id,
            workflow_id=workflow.id,
            input_dataset_id=input_dataset.id,
            output_dataset_id=output_dataset.id,
            working_dir=str(working_dir),
        )

        # Test get_workflowtask_status endpoint
        res = await client.get(
            f"api/v1/project/{project.id}/dataset/{output_dataset.id}/status/"
        )
        debug(res.status_code)
        assert res.status_code == 200
        statuses = res.json()["status"]
        debug(statuses)
        for expected_status, IDs in RESULTS.items():
            for ID in IDs:
                ID_str = str(ID)  # JSON-object keys can only be strings
                assert statuses[ID_str] == expected_status


async def test_get_workflowtask_status_fail(
    db,
    MockCurrentUser,
    tmp_path,
    project_factory,
    task_factory,
    dataset_factory,
    workflow_factory,
    job_factory,
    client,
):
    """
    Fail due to multiple ongoing jobs being associated with a given dataset
    """

    async with MockCurrentUser(persist=True) as user:
        project = await project_factory(user)
        workflow = await workflow_factory(project_id=project.id, name="WF")
        task = await task_factory()
        await workflow.insert_task(task_id=task.id, db=db)
        dataset = await dataset_factory(project_id=project.id)

        # Create *two* jobs in relation with dataset
        for ind in range(2):
            job = await job_factory(  # noqa
                project_id=project.id,
                workflow_id=workflow.id,
                input_dataset_id=dataset.id,
                output_dataset_id=dataset.id,
                working_dir=str(tmp_path / "working_dir"),
            )

        # Test export_history_as_workflow failure
        res = await client.get(
            f"api/v1/project/{project.id}/dataset/{dataset.id}/status/"
        )
        assert res.status_code == 422
        debug(res.json()["detail"])


async def test_export_history_as_workflow_fail(
    db,
    MockCurrentUser,
    tmp_path,
    project_factory,
    task_factory,
    dataset_factory,
    workflow_factory,
    job_factory,
    client,
):
    """
    Fail because of existing jobs linked to the dataset
    """
    async with MockCurrentUser(persist=True) as user:
        project = await project_factory(user)
        workflow = await workflow_factory(project_id=project.id, name="WF")
        task = await task_factory()
        await workflow.insert_task(task_id=task.id, db=db)
        dataset = await dataset_factory(project_id=project.id)

        # Create job in relation with dataset
        job = await job_factory(  # noqa
            project_id=project.id,
            workflow_id=workflow.id,
            input_dataset_id=dataset.id,
            output_dataset_id=dataset.id,
            working_dir=str(tmp_path / "working_dir"),
        )

        # Test export_history_as_workflow failure
        res = await client.get(
            f"api/v1/project/{project.id}/"
            f"dataset/{dataset.id}/export_history/"
        )
        assert res.status_code == 422
        debug(res.json()["detail"])
        assert res.json()["detail"].startswith("Cannot export history")

        # Create second job in relation with dataset
        job = await job_factory(  # noqa
            project_id=project.id,
            workflow_id=workflow.id,
            input_dataset_id=dataset.id,
            output_dataset_id=dataset.id,
            working_dir=str(tmp_path / "working_dir"),
        )

        # Test export_history_as_workflow failure
        res = await client.get(
            f"api/v1/project/{project.id}/"
            f"dataset/{dataset.id}/export_history/"
        )
        assert res.status_code == 422
        debug(res.json()["detail"])
        assert res.json()["detail"].startswith("Cannot export history")


async def test_assemble_history_failed_job_fail(
    db,
    MockCurrentUser,
    tmp_path,
    project_factory,
    dataset_factory,
    workflow_factory,
    job_factory,
    task_factory,
    caplog,
):
    """
    Test a failing branch for assemble_history_failed_job, where the failed
    task cannot be identified.
    """
    async with MockCurrentUser(persist=True) as user:
        project = await project_factory(user)
        workflow = await workflow_factory(project_id=project.id, name="WF")
        task = await task_factory()
        wftask = await workflow.insert_task(task_id=task.id, db=db)
        dataset = await dataset_factory(project_id=project.id)
        job = await job_factory(
            project_id=project.id,
            workflow_id=workflow.id,
            input_dataset_id=dataset.id,
            output_dataset_id=dataset.id,
            working_dir=str(tmp_path / "working_dir"),
        )

    from pathlib import Path

    Path(job.working_dir).mkdir()
    tmp_history = [dict(workflowtask={"id": wftask.id})]
    with (Path(job.working_dir) / METADATA_FILENAME).open("w") as fp:
        json.dump(dict(history=tmp_history), fp)

    logger = logging.getLogger(None)
    caplog.clear()
    history = assemble_history_failed_job(job, dataset, workflow, logger)
    assert "Cannot identify the failed task" in caplog.text
    debug(history)
    assert history == tmp_history