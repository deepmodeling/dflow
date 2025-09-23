import logging
import os
import sys
from copy import deepcopy
from typing import Dict, List, Optional, Union

from .common import (input_artifact_pattern, input_parameter_pattern,
                     task_output_artifact_pattern,
                     task_output_parameter_pattern)
from .config import config, s3_config
from .context_syntax import GLOBAL_CONTEXT
from .io import Inputs, Outputs, OutputArtifact
from .op_template import OPTemplate
from .step import add_slices
from .task import Task

try:
    from argo.workflows.client import (V1alpha1DAGTemplate, V1alpha1Metadata,
                                       V1alpha1Template)
except Exception:
    pass


class DAG(OPTemplate):
    """
    DAG

    Args:
        name: the name of the dag
        inputs: inputs in the template
        outputs: outputs in the template
        tasks: a list of tasks
        memoize_key: memoized key of the dag
        annotations: annotations for the OP template
        parallelism: maximum number of running pods for the OP template
        """

    def __init__(
            self,
            name: Optional[str] = None,
            inputs: Optional[Inputs] = None,
            outputs: Optional[Outputs] = None,
            tasks: Optional[List[Task]] = None,
            memoize_key: Optional[str] = None,
            annotations: Dict[str, str] = None,
            parallelism: Optional[int] = None,
    ) -> None:
        super().__init__(name=name, inputs=inputs, outputs=outputs,
                         memoize_key=memoize_key, annotations=annotations)
        self.parallelism = parallelism
        self.tasks = []
        if tasks is not None:
            for task in tasks:
                self.add(task)

    @classmethod
    def from_dict(cls, d, templates):
        kwargs = {
            "name": d.get("name", None),
            "inputs": Inputs.from_dict(d.get("inputs", {})),
            "outputs": Outputs.from_dict(d.get("outputs", {})),
            "memoize_key": d.get("memoize", {}).get("key", None),
            "annotations": d.get("metadata", {}).get("annotations", None),
            "parallelism": d.get("parallelism", None),
        }
        tasks = {task["name"]: Task.from_dict(task, templates)
                 for task in d.get("dag", {}).get("tasks", [])}
        for task in tasks.values():
            task.dependencies = [tasks[t] for t in task.dependencies]
        kwargs["tasks"] = list(tasks.values())
        return cls(**kwargs)

    @classmethod
    def from_graph(cls, graph, templates):
        assert graph.pop("type") == "DAG"
        graph["inputs"] = Inputs.from_graph(graph.get("inputs", {}))
        tasks = graph.pop("tasks")
        outputs = graph.pop("outputs", {})

        obj = cls(**graph)
        templates[graph["name"]] = obj

        task_dict = {}
        for t in tasks:
            task = Task.from_graph(t, templates)
            obj.add(task)
            task_dict[task.name] = task

        # replace variable references with pointers
        for task in obj.tasks:
            for name, par in task.inputs.parameters.items():
                value = getattr(par, "value", None)
                if isinstance(value, str):
                    match = input_parameter_pattern.match(value)
                    if match:
                        task.set_parameters({name: obj.inputs.parameters[
                            match.group(1)]})
                    match = task_output_parameter_pattern.match(value)
                    if match:
                        task.set_parameters({name: task_dict[match.group(
                            1)].outputs.parameters[match.group(2)]})
            for name, art in task.inputs.artifacts.items():
                source = art.source
                if isinstance(source, str):
                    match = input_artifact_pattern.match(source)
                    if match:
                        task.set_artifacts({name: obj.inputs.artifacts[
                            match.group(1)]})
                    match = task_output_artifact_pattern.match(source)
                    if match:
                        task.set_artifacts({name: task_dict[match.group(
                            1)].outputs.artifacts[match.group(2)]})

        obj.outputs = Outputs.from_graph(outputs)
        # replace variable references with pointers
        for par in obj.outputs.parameters.values():
            _from = par.value_from_parameter
            if isinstance(_from, str):
                match = input_parameter_pattern.match(_from)
                if match:
                    par.value_from_parameter = obj.inputs.parameters[
                        match.group(1)]
                match = task_output_parameter_pattern.match(_from)
                if match:
                    par.value_from_parameter = task_dict[match.group(1)].\
                        outputs.parameters[match.group(2)]
        for art in obj.outputs.artifacts.values():
            _from = art._from
            if isinstance(_from, str):
                match = input_artifact_pattern.match(_from)
                if match:
                    art._from = obj.inputs.artifacts[match.group(1)]
                match = task_output_artifact_pattern.match(_from)
                if match:
                    art._from = task_dict[match.group(1)].outputs.\
                        artifacts[match.group(2)]
        return obj

    def __iter__(self):
        return iter(self.tasks)

    def add(
            self,
            task: Union[Task, List[Task]],
    ) -> None:
        """
        Add a task or a list of tasks to the dag

        Args:
            task: a task or a list of tasks to be added to the dag
        """
        if not isinstance(task, list):
            task = [task]

        for t in task:
            assert isinstance(t, Task)
            if t.prepare_step is not None:
                self.tasks.append(t.prepare_step)
            if t.parallelism is not None:
                if self.parallelism is None:
                    self.parallelism = t.parallelism
                else:
                    self.parallelism = min(self.parallelism, t.parallelism)
                    logging.warn("Multiple tasks specified parallelism, small"
                                 "er one %s will be used" % self.parallelism)
            self.tasks.append(t)
            if t.check_step is not None:
                self.tasks.append(t.check_step)

    def convert_to_argo(self, memoize_prefix=None,
                        memoize_configmap="dflow", context=None):
        argo_tasks = []
        templates = []
        assert len(self.tasks) > 0, "Dag %s is empty" % self.name
        for task in self.tasks:
            argo_tasks.append(task.convert_to_argo(context))
            templates.append(task.template)
            templates += [hook.template for hook in task.hooks.values()]

        self.handle_key(memoize_prefix, memoize_configmap)
        argo_template = \
            V1alpha1Template(name=self.name,
                             metadata=V1alpha1Metadata(
                                 annotations=self.annotations),
                             dag=V1alpha1DAGTemplate(
                                 tasks=argo_tasks,
                             ),
                             inputs=self.inputs.convert_to_argo(),
                             outputs=self.outputs.convert_to_argo(),
                             memoize=self.memoize,
                             parallelism=self.parallelism)
        return argo_template, templates

    def convert_to_graph(self):
        graph_tasks = []
        templates = []
        for task in self.tasks:
            if not task.name.endswith("-init-artifact") and \
                not task.name.endswith("-check-num-success") and \
                    not task.name.endswith("-check-success-ratio"):
                graph_tasks.append(task.convert_to_graph())
                templates.append(task.template)

        return {
            "type": "DAG",
            "name": self.name,
            "annotations": self.annotations,
            "tasks": graph_tasks,
            "inputs": self.inputs.convert_to_graph(),
            "outputs": self.outputs.convert_to_graph(),
            "parallelism": self.parallelism,
        }, templates

    def resolve(self, pool, futures):
        import concurrent.futures
        self_copy = deepcopy(self)
        for task in self.waiting.copy():
            ready = True
            for dep in task.dependencies:
                if dep in self.finished:
                    if getattr(dep, "phase", None) != "Succeeded":
                        self.waiting.remove(task)
                        self.finished.append(task)
                        ready = False
                        break
                else:
                    ready = False
                    break
            if ready:
                task.phase = "Pending"
                i = self.tasks.index(task)
                try:
                    future = pool.submit(
                        task.run_with_config, self_copy, self.context, config,
                        s3_config, self.cwd, str(i))
                except concurrent.futures.process.BrokenProcessPool as e:
                    # retrieve exception of subprocess before exit
                    for future in concurrent.futures.as_completed(futures):
                        future.result()
                    raise e
                futures[future] = i
                self.waiting.remove(task)
                self.running.append(task)

    def run(self, workflow_id=None, context=None, stepdir=None):
        self.workflow_id = workflow_id
        self.stepdir = stepdir
        self.context = context
        import concurrent.futures
        self.cwd = os.getcwd()
        max_workers = config["debug_pool_workers"]
        if max_workers == -1:
            max_workers = len(self.tasks)
        if max_workers is None:
            max_workers = os.cpu_count() or 1
        max_workers = min(max_workers, len(self.tasks)) or 1
        pool = concurrent.futures.ProcessPoolExecutor(max_workers)
        futures = {}
        self.waiting = [task for task in self]
        self.running = []
        self.finished = []
        self.resolve(pool, futures)

        while len(self.running) > 0:
            future = next(concurrent.futures.as_completed(futures))
            j = futures.pop(future)
            try:
                phase, pars, arts = future.result()
            except Exception:
                import traceback
                traceback.print_exc()
                self.tasks[j].phase = "Failed"
                if not self.tasks[j].continue_on_failed:
                    if sys.version_info.minor >= 9:
                        pool.shutdown(wait=False)
                    else:
                        pool.shutdown(wait=True)
                    raise RuntimeError("Task %s failed" % self.tasks[j])
            else:
                for name, value in pars.items():
                    self.tasks[j].outputs.parameters[
                        name].value = value
                for name, path in arts.items():
                    if name not in self.tasks[j].outputs.artifacts:
                        self.tasks[j].outputs.artifacts[name] = \
                            OutputArtifact()
                    self.tasks[j].outputs.artifacts[
                        name].local_path = path
                self.tasks[j].phase = phase
                logging.info("Outputs of %s collected" % self.tasks[j])
            self.running.remove(self.tasks[j])
            self.finished.append(self.tasks[j])
            self.resolve(pool, futures)

        if sys.version_info.minor >= 9:
            pool.shutdown(wait=False)
        else:
            pool.shutdown(wait=True)
        assert len(self.finished) == len(self.tasks), "cyclic graph"

    def add_slices(self, slices, layer=0):
        add_slices(self, slices, layer=layer)

    def copy(self):
        new_template = self.deepcopy()
        for task, new_task in zip(self.tasks, new_template.tasks):
            new_task.template = task.template
        return new_template

    def __enter__(self) -> 'DAG':
        GLOBAL_CONTEXT.in_context = True
        GLOBAL_CONTEXT.current_workflow = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        GLOBAL_CONTEXT.in_context = False
