import logging
import os
import time
from copy import deepcopy
from typing import Dict, List, Optional, Union

from .common import (input_artifact_pattern, input_parameter_pattern,
                     step_output_artifact_pattern,
                     step_output_parameter_pattern)
from .config import config, s3_config
from .context_syntax import GLOBAL_CONTEXT
from .io import Inputs, Outputs, OutputArtifact
from .op_template import OPTemplate
from .step import Step, add_slices
from .utils import ProcessPoolExecutor

try:
    from argo.workflows.client import V1alpha1Metadata, V1alpha1Template
except Exception:
    pass


class Steps(OPTemplate):
    """
    Steps

    Args:
        name: the name of the steps
        inputs: inputs in the template
        outputs: outputs in the template
        steps: a sequential list of steps
        memoize_key: memoized key of the steps
        annotations: annotations for the OP template
        parallelism: maximum number of running pods for the OP template
        """

    def __init__(
            self,
            name: Optional[str] = None,
            inputs: Optional[Inputs] = None,
            outputs: Optional[Outputs] = None,
            steps: List[Union[Step, List[Step]]] = None,
            memoize_key: Optional[str] = None,
            annotations: Dict[str, str] = None,
            parallelism: Optional[int] = None,
    ) -> None:
        super().__init__(name=name, inputs=inputs, outputs=outputs,
                         memoize_key=memoize_key, annotations=annotations)
        self.parallelism = parallelism
        self.steps = []
        if steps is not None:
            for step in steps:
                self.add(step)

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
        kwargs["steps"] = [[Step.from_dict(ps, templates) for ps in step]
                           for step in d.get("steps", [[]])]
        return cls(**kwargs)

    def __iter__(self):
        return iter(self.steps)

    def add(
            self,
            step: Union[Step, List[Step]],
    ) -> None:
        """
        Add a step or a list of parallel steps to the steps

        Args:
            step: a step or a list of parallel steps to be added to the
                entrypoint of the workflow
        """
        assert isinstance(step, (Step, list))
        if isinstance(step, Step):
            if step.prepare_step is not None:
                self.steps.append(step.prepare_step)
        elif isinstance(step, list):
            prepare_steps = [ps.prepare_step for ps in step
                             if ps.prepare_step is not None]
            if prepare_steps:
                self.steps.append(prepare_steps)
        for ps in [step] if isinstance(step, Step) else step:
            if ps.parallelism is not None:
                if self.parallelism is None:
                    self.parallelism = ps.parallelism
                else:
                    self.parallelism = min(self.parallelism, ps.parallelism)
                    logging.warn("Multiple steps specified parallelism, small"
                                 "er one %s will be used" % self.parallelism)
        self.steps.append(step)
        if isinstance(step, Step):
            if step.check_step is not None:
                self.steps.append(step.check_step)
        elif isinstance(step, list):
            check_steps = [ps.check_step for ps in step
                           if ps.check_step is not None]
            if check_steps:
                self.steps.append(check_steps)

    def convert_to_argo(self, memoize_prefix=None,
                        memoize_configmap="dflow", context=None):
        argo_steps = []
        templates = []
        assert len(self.steps) > 0, "Steps %s is empty" % self.name
        for step in self.steps:
            # each step of steps should be a list of parallel steps, if not,
            # create a sigleton
            if not isinstance(step, list):
                step = [step]
            argo_parallel_steps = []
            for ps in step:
                argo_parallel_steps.append(ps.convert_to_argo(context))
                # template may change after conversion
                templates.append(ps.template)
                templates += [hook.template for hook in ps.hooks.values()]
            argo_steps.append(argo_parallel_steps)

        self.handle_key(memoize_prefix, memoize_configmap)
        argo_template = \
            V1alpha1Template(name=self.name,
                             metadata=V1alpha1Metadata(
                                 annotations=self.annotations),
                             steps=argo_steps,
                             inputs=self.inputs.convert_to_argo(),
                             outputs=self.outputs.convert_to_argo(),
                             memoize=self.memoize,
                             parallelism=self.parallelism)
        return argo_template, templates

    def convert_to_graph(self):
        graph_steps = []
        templates = []
        for step in self.steps:
            if not isinstance(step, list):
                step = [step]
            graph_parallel_steps = []
            for ps in step:
                if not ps.name.endswith("-init-artifact") and \
                    not ps.name.endswith("-check-num-success") and \
                        not ps.name.endswith("-check-success-ratio"):
                    graph_parallel_steps.append(ps.convert_to_graph())
                    templates.append(ps.template)
            if len(graph_parallel_steps) > 0:
                graph_steps.append(graph_parallel_steps)

        return {
            "type": "Steps",
            "name": self.name,
            "annotations": self.annotations,
            "steps": graph_steps,
            "inputs": self.inputs.convert_to_graph(),
            "outputs": self.outputs.convert_to_graph(),
            "parallelism": self.parallelism,
        }, templates

    @classmethod
    def from_graph(cls, graph, templates):
        assert graph.pop("type") == "Steps"
        graph["inputs"] = Inputs.from_graph(graph.get("inputs", {}))
        steps = graph.pop("steps")
        outputs = graph.pop("outputs", {})

        obj = cls(**graph)
        templates[graph["name"]] = obj

        step_dict = {}
        for step in steps:
            parallel_steps = []
            for ps in step:
                s = Step.from_graph(ps, templates)
                parallel_steps.append(s)
                step_dict[s.name] = s
            obj.add(parallel_steps)

        # replace variable references with pointers
        for step in obj.steps:
            for ps in step:
                for name, par in ps.inputs.parameters.items():
                    value = getattr(par, "value", None)
                    if isinstance(value, str):
                        match = input_parameter_pattern.match(value)
                        if match:
                            ps.set_parameters({
                                name: obj.inputs.parameters[match.group(1)]})
                        match = step_output_parameter_pattern.match(value)
                        if match:
                            ps.set_parameters({name: step_dict[match.group(
                                1)].outputs.parameters[match.group(2)]})
                for name, art in ps.inputs.artifacts.items():
                    source = art.source
                    if isinstance(source, str):
                        match = input_artifact_pattern.match(source)
                        if match:
                            ps.set_artifacts({
                                name: obj.inputs.artifacts[match.group(1)]})
                        match = step_output_artifact_pattern.match(source)
                        if match:
                            ps.set_artifacts({name: step_dict[match.group(
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
                match = step_output_parameter_pattern.match(_from)
                if match:
                    par.value_from_parameter = step_dict[match.group(1)].\
                        outputs.parameters[match.group(2)]
        for art in obj.outputs.artifacts.values():
            _from = art._from
            if isinstance(_from, str):
                match = input_artifact_pattern.match(_from)
                if match:
                    art._from = obj.inputs.artifacts[match.group(1)]
                match = step_output_artifact_pattern.match(_from)
                if match:
                    art._from = step_dict[match.group(1)].outputs.\
                        artifacts[match.group(2)]
        return obj

    def run(self, workflow_id=None, context=None, stepdir=None):
        self.workflow_id = workflow_id
        self.stepdir = stepdir
        for ii, step in enumerate(self):
            if isinstance(step, list):
                import concurrent.futures
                cwd = os.getcwd()
                max_workers = config["debug_pool_workers"]
                if max_workers == -1:
                    max_workers = len(step)
                if max_workers is None:
                    max_workers = os.cpu_count() or 1
                max_workers = min(max_workers, len(step)) or 1
                with ProcessPoolExecutor(max_workers) as pool:
                    futures = []
                    self_copy = deepcopy(self)
                    for i, ps in enumerate(step):
                        ps.phase = "Pending"
                        try:
                            future = pool.submit(
                                ps.run_with_config, self_copy, context, config,
                                s3_config, cwd, "%s-%s" % (ii, i))
                        except concurrent.futures.process.BrokenProcessPool \
                                as e:
                            # retrieve exception of subprocess before exit
                            for future in concurrent.futures.as_completed(
                                    futures):
                                future.result()
                            raise e
                        futures.append(future)
                        if config["debug_batch_size"] and i != len(step) - 1 \
                                and (i+1) % config["debug_batch_size"] == 0:
                            logging.info(
                                "Wait %s seconds before submitting next "
                                "batch" % config["debug_batch_interval"])
                            time.sleep(config["debug_batch_interval"])

                    for future in concurrent.futures.as_completed(futures):
                        j = futures.index(future)
                        try:
                            phase, pars, arts = future.result()
                        except Exception:
                            import traceback
                            traceback.print_exc()
                            step[j].phase = "Failed"
                            if not step[j].continue_on_failed:
                                raise RuntimeError("Step %s failed" % step[j])
                        else:
                            for name, value in pars.items():
                                step[j].outputs.parameters[
                                    name].value = value
                            for name, path in arts.items():
                                if name not in step[j].outputs.artifacts:
                                    step[j].outputs.artifacts[name] = \
                                        OutputArtifact()
                                step[j].outputs.artifacts[
                                    name].local_path = path
                            logging.info("Outputs of %s collected" % step[j])
            else:
                step.run(self, context, "%s-0" % ii)

    def add_slices(self, slices, layer=0):
        add_slices(self, slices, layer=layer)

    def copy(self):
        new_template = self.deepcopy()
        for step, new_step in zip(self.steps, new_template.steps):
            if isinstance(new_step, list):
                for ps, new_ps in zip(step, new_step):
                    new_ps.template = ps.template
            else:
                new_step.template = step.template
        return new_template

    def __enter__(self) -> 'Steps':
        GLOBAL_CONTEXT.in_context = True
        GLOBAL_CONTEXT.current_workflow = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        GLOBAL_CONTEXT.in_context = False
