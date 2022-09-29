from typing import Dict
from typing import Optional

import typeguard
from parsl.app.python import PythonApp
from parsl.config import Config
from parsl.dataflow.dflow import DataFlowKernel
from parsl.dataflow.dflow import DataFlowKernelLoader


class LocalDataFlowKernelLoader(DataFlowKernelLoader):
    # NOTE: Ok to initialise with mutable as it is a singleton
    _local_dfk: Dict[str, DataFlowKernel] = {}

    @classmethod
    def clear(cls, dfk_id: str):
        # TODO: also cleanup
        cls._local_dfk.pop(dfk_id)

    @classmethod
    @typeguard.typechecked
    def load(
        cls, dfk_id: str, config: Optional[Config] = None
    ) -> DataFlowKernel:
        if dfk_id in cls._local_dfk:
            raise RuntimeError(f"Config has already been loaded for {dfk_id=}")
        else:
            if config is None:
                cls._local_dfk[dfk_id] = DataFlowKernel(Config())
            else:
                cls._local_dfk[dfk_id] = DataFlowKernel(config)

        return cls._local_dfk[dfk_id]

    @classmethod
    def wait_for_current_tasks(cls, dfk_id: str) -> None:
        """
        Waits for all tasks in the task list to be completed, by waiting
        for their AppFuture to be completed. This method will not necessarily
        wait for any tasks added after cleanup has started such as data
        stageout.
        """
        cls.dfk(dfk_id=dfk_id).wait_for_current_tasks()

    @classmethod
    def dfk(cls, dfk_id: str) -> DataFlowKernel:
        """Return the currently-loaded DataFlowKernel."""
        try:
            return cls._local_dfk[dfk_id]
        except KeyError:
            from os import getpid, getppid

            raise RuntimeError(
                f"No dfk with {dfk_id=}. Did you load the config?"
                f"\nERROR: {id(cls)=}"
                f"\nERROR: {id(cls._local_dfk)=}"
                f"\nERROR: {getpid()=}"
                f"\nERROR: {getppid()=}"
            )


class LocalPythonApp(PythonApp):
    def __init__(self, *args, dfk_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not dfk_id:
            raise ValueError("Must specify dfk_id")
        self.dfk_id = dfk_id

    def __call__(self, *args, **kwargs):
        self.data_flow_kernel = LocalDataFlowKernelLoader.dfk(
            dfk_id=self.dfk_id
        )
        return super().__call__(*args, **kwargs)
