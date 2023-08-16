import os
from pathlib import Path

from dflow import Step, Workflow
from dflow.plugins.bohrium import BohriumDatasetsArtifact
from dflow.plugins.dispatcher import DispatcherExecutor
from dflow.python import OP, OPIO, Artifact, OPIOSign, PythonOPTemplate


class Hello(OP):
    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            'foo': Artifact(Path),
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign()

    @OP.exec_sign_check
    def execute(
            self,
            op_in: OPIO,
    ) -> OPIO:
        os.system("ls -l %s" % op_in["foo"])
        return OPIO()


if __name__ == "__main__":
    dispatcher_executor = DispatcherExecutor(
        machine_dict={
            "batch_type": "Bohrium",
            "context_type": "Bohrium",
        },
    )

    wf = Workflow(name="datasets")
    art = BohriumDatasetsArtifact("/bohr/water-example-m7kb/v1")
    step = Step(
        name="step",
        template=PythonOPTemplate(Hello, image="python:3.8"),
        artifacts={"foo": art},
        executor=dispatcher_executor,
    )
    wf.add(step)
    wf.submit()
