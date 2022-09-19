import logging
import re
from copy import deepcopy
from typing import Any, Dict, List, Union

import jsonpickle

from .common import LocalArtifact, S3Artifact
from .config import config
from .context_syntax import GLOBAL_CONTEXT
from .executor import Executor
from .io import (PVC, ArgoVar, InputArtifact, InputParameter, OutputArtifact,
                 OutputParameter)
from .op_template import OPTemplate, PythonScriptOPTemplate, ShellOPTemplate
from .resource import Resource
from .util_ops import CheckNumSuccess, CheckSuccessRatio, InitArtifactForSlices
from .utils import catalog_of_artifact, randstr, upload_artifact

try:
    from argo.workflows.client import (V1alpha1Arguments, V1alpha1ContinueOn,
                                       V1alpha1ResourceTemplate,
                                       V1alpha1WorkflowStep, V1VolumeMount)

    from .client import V1alpha1Sequence
except Exception:
    V1alpha1Sequence = object


uploaded_python_packages = []


def argo_range(
        *args,
) -> ArgoVar:
    """
    Return a str representing a range of integer in Argo
    It receives 1-3 arguments, which is similar to the function `range` in
        Python
    Each argument can be Argo parameter
    """
    if config["mode"] == "debug":
        args = tuple(i.value if isinstance(i, (InputParameter, OutputParameter
                                               )) else i for i in args)
        for i in range(len(args)):
            if isinstance(args[i], (InputParameter, OutputParameter)):
                args[i] = args[i].value
        return list(range(*args))
    start = 0
    step = 1
    if len(args) == 1:
        end = args[0]
    elif len(args) == 2:
        start = args[0]
        end = args[1]
    elif len(args) == 3:
        start = args[0]
        end = args[1]
        step = args[2]
    else:
        raise TypeError("Expected 1-3 arguments, got %s" % len(args))
    if isinstance(start, (InputParameter, OutputParameter)):
        start = "sprig.atoi(%s)" % start.expr
    if isinstance(step, (InputParameter, OutputParameter)):
        step = "sprig.atoi(%s)" % step.expr
    if isinstance(end, (InputParameter, OutputParameter)):
        end = "sprig.atoi(%s)" % end.expr
    return ArgoVar("toJson(sprig.untilStep(%s, %s, %s))" % (start, end, step))


def argo_sequence(
        count: Union[int, ArgoVar] = None,
        start: Union[int, ArgoVar] = None,
        end: Union[int, ArgoVar] = None,
        format: str = None,
) -> V1alpha1Sequence:
    """
    Return a numeric sequence in Argo

    Args:
        count: number of elements in the sequence (default: 0), not to be used
            with end, can be an Argo parameter
        start: number at which to start the sequence (default: 0), can be an
            Argo parameter
        end: number at which to end the sequence (default: 0), not to be used
            with count, can be an Argo parameter
        format: a printf format string to format the value in the sequence
    """
    if isinstance(count, ArgoVar):
        count = "{{=%s}}" % count.expr
    if isinstance(start, ArgoVar):
        start = "{{=%s}}" % start.expr
    if isinstance(end, ArgoVar):
        end = "{{=%s}}" % end.expr
    return V1alpha1Sequence(count=count, start=start, end=end, format=format)


def argo_len(
        param: Union[ArgoVar, S3Artifact],
) -> ArgoVar:
    """
    Return the length of a list which is an Argo parameter

    Args:
        param: the Argo parameter which is a list
    """
    if config["mode"] == "debug":
        return len(param.value)
    if isinstance(param, S3Artifact):
        try:
            path_list = catalog_of_artifact(param)
            if path_list:
                param.path_list = path_list
        except Exception:
            pass
        return ArgoVar(str(len(param.path_list)))
    if isinstance(param, InputArtifact):
        assert config["save_path_as_parameter"]
        return ArgoVar("len(sprig.fromJson(%s))" %
                       param.get_path_list_parameter())
    elif isinstance(param, OutputArtifact):
        assert config["save_path_as_parameter"]
        return ArgoVar("len(sprig.fromJson(%s))" %
                       param.get_path_list_parameter())
    else:
        return ArgoVar("len(sprig.fromJson(%s))" % param.expr)


class Step:
    """
    Step

    Args:
        name: the name of the step
        template: OP template the step uses
        parameters: input parameters passed to the step as arguments
        artifacts: input artifacts passed to the step as arguments
        when: conditional step if the condition is satisfied
        with_param: generate parallel steps with respect to a list as a
            parameter
        continue_on_failed: continue if the step fails
        continue_on_num_success: continue if the success number of the
            generated parallel steps greater than certain number
        continue_on_success_ratio: continue if the success ratio of the
            generated parallel steps greater than certain number
        with_sequence: generate parallel steps with respect to a sequence
        key: the key of the step
        executor: define the executor to execute the script
        use_resource: use k8s resource
        util_image: image for utility step
        util_image_pull_policy: image pull policy for utility step
        util_command: command for utility step
        parallelism: parallelism for sliced step
    """

    def __init__(
            self,
            name: str,
            template: OPTemplate,
            parameters: Dict[str, Any] = None,
            artifacts: Dict[str, Union[S3Artifact,
                                       InputArtifact, OutputArtifact]] = None,
            when: str = None,
            with_param: Union[str, list,
                              InputParameter, OutputParameter] = None,
            continue_on_failed: bool = False,
            continue_on_num_success: int = None,
            continue_on_success_ratio: float = None,
            with_sequence: V1alpha1Sequence = None,
            key: str = None,
            executor: Executor = None,
            use_resource: Resource = None,
            util_image: str = None,
            util_image_pull_policy: str = None,
            util_command: Union[str, List[str]] = None,
            parallelism: int = None,
            **kwargs,
    ) -> None:
        self.name = name
        self.id = self.name
        self.template = template
        self.inputs = deepcopy(self.template.inputs)
        self.outputs = deepcopy(self.template.outputs)
        self.inputs.set_step(self)
        self.outputs.set_step(self)
        self.continue_on_failed = continue_on_failed
        self.continue_on_num_success = continue_on_num_success
        self.continue_on_success_ratio = continue_on_success_ratio
        self.check_step = None
        self.prepare_step = None

        if parameters is not None:
            self.set_parameters(parameters)

        if artifacts is not None:
            self.set_artifacts(artifacts)

        self.when = when
        self.with_param = with_param
        self.with_sequence = with_sequence
        self.key = key
        self.executor = executor
        self.use_resource = use_resource
        if util_image is None:
            util_image = config["util_image"]
        self.util_image = util_image
        if util_image_pull_policy is None:
            util_image_pull_policy = config["util_image_pull_policy"]
        self.util_image_pull_policy = util_image_pull_policy
        if isinstance(util_command, str):
            util_command = [util_command]
        self.util_command = util_command
        self.parallelism = parallelism

        if hasattr(self.template, "python_packages") and \
                self.template.python_packages:
            hit = list(filter(lambda x: x[0] == self.template.python_packages,
                              uploaded_python_packages))
            if len(hit) > 0:
                self.set_artifacts({"dflow_python_packages": hit[0][1]})
            else:
                artifact = upload_artifact(self.template.python_packages)
                self.set_artifacts({"dflow_python_packages": artifact})
                uploaded_python_packages.append(
                    (self.template.python_packages, artifact))

        if self.key is not None:
            self.template.inputs.parameters["dflow_key"] = InputParameter(
                value="")
            self.inputs.parameters["dflow_key"] = InputParameter(
                value=str(self.key))

        new_template = None

        if hasattr(self.template, "slices") and self.template.slices is not \
                None and (self.template.slices.output_artifact or (
                    self.template.slices.sub_path and
                    self.template.slices.input_artifact)):
            if new_template is None:
                new_template = deepcopy(self.template)
                new_template.name = self.template.name + "-" + randstr()
            init_template = InitArtifactForSlices(
                new_template.name, self.util_image, self.util_command,
                self.util_image_pull_policy, self.key,
                self.template.slices.output_artifact,
                self.template.slices.sub_path,
                self.template.slices.input_artifact)
            if self.key is not None:
                new_template.inputs.parameters["dflow_group_key"] = \
                    InputParameter(value="")
                self.inputs.parameters["dflow_group_key"] = InputParameter(
                    value=re.sub("{{item.*}}", "group", str(self.key)))
                # For the case of reusing sliced steps, ensure that the output
                # artifacts are reused
                for name in new_template.slices.output_artifact:
                    new_template.outputs.artifacts[name].save.append(
                        S3Artifact(key="{{workflow.name}}/{{inputs."
                                   "parameters.dflow_group_key}}/%s" % name))
            else:
                new_template.inputs.parameters["dflow_artifact_key"] = \
                    InputParameter(value="")
                for name in new_template.slices.output_artifact:
                    new_template.outputs.artifacts[name].save.append(
                        S3Artifact(key="{{inputs.parameters."
                                   "dflow_artifact_key}}/%s" % name))

            if self.key is not None:
                self.prepare_step = self.__class__(
                    name="%s-init-artifact" % self.name,
                    template=init_template,
                    parameters={"dflow_group_key": re.sub("{{item.*}}",
                                                          "group",
                                                          str(self.key))})
            else:
                self.prepare_step = self.__class__(
                    name="%s-init-artifact" % self.name,
                    template=init_template)
                self.inputs.parameters["dflow_artifact_key"] = InputParameter(
                    value=self.prepare_step.outputs.parameters[
                        "dflow_artifact_key"])

            if new_template.slices.sub_path and \
                    new_template.slices.input_artifact:
                for name in new_template.slices.input_artifact:
                    self.inputs.parameters["dflow_%s_sub_path" %
                                           name].value = "{{item.%s}}" % name
                    # step cannot resolve
                    # {{inputs.parameters.dflow_%s_sub_path}}
                    self.inputs.artifacts[name].path = None
                    v = self.inputs.artifacts[name].source
                    if isinstance(v, S3Artifact):
                        self.prepare_step.inputs.artifacts[name].source = \
                            v.sub_path(config["catalog_dir_name"])
                        self.inputs.artifacts[name].source = \
                            v.sub_path("{{item.%s}}" % name)
                    elif isinstance(v, (InputArtifact, OutputArtifact,
                                        LocalArtifact)):
                        self.prepare_step.inputs.artifacts[name].source = v
                        self.inputs.artifacts[name].sub_path = \
                            "{{item.%s}}" % name
                self.with_param = self.prepare_step.outputs.parameters[
                    "dflow_slices_path"]

            for name in new_template.slices.output_artifact:
                self.outputs.artifacts[name].redirect = \
                    self.prepare_step.outputs.artifacts[name]

        pvc_arts = []
        for art in self.inputs.artifacts.values():
            if isinstance(art.source, PVC):
                pvc_arts.append((art.source, art))

        if len(pvc_arts) > 0:
            if new_template is None:
                new_template = deepcopy(self.template)
                new_template.name = self.template.name + "-" + randstr()
            if (isinstance(new_template, ShellOPTemplate)):
                for pvc, art in pvc_arts:
                    del new_template.inputs.artifacts[art.name]
                    new_template.script = "ln -s /tmp/mnt/%s %s\n" % (
                        pvc.subpath, art.path) + new_template.script
                    new_template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    new_template.pvcs.append(pvc)
            elif (isinstance(new_template, PythonScriptOPTemplate)):
                for pvc, art in pvc_arts:
                    del new_template.inputs.artifacts[art.name]
                    new_template.script = \
                        "os.system('ln -s /tmp/mnt/%s %s')\n" % (
                            pvc.subpath, art.path) + new_template.script
                    new_template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    new_template.pvcs.append(pvc)
                new_template.script = "import os\n" + new_template.script
            else:
                raise RuntimeError(
                    "Unsupported type of OPTemplate to mount PVC")

        pvc_arts = []
        for art in self.outputs.artifacts.values():
            for save in art.save:
                if isinstance(save, PVC):
                    pvc_arts.append((save, art))

        if len(pvc_arts) > 0:
            if new_template is None:
                new_template = deepcopy(self.template)
                new_template.name = self.template.name + "-" + randstr()
            if (isinstance(new_template, ShellOPTemplate)):
                new_template.script += "\n"
                for pvc, art in pvc_arts:
                    new_template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    new_template.script += "cp -r %s /tmp/mnt/%s\n" % (
                        art.path, pvc.subpath)
                    new_template.pvcs.append(pvc)
            elif (isinstance(new_template, PythonScriptOPTemplate)):
                new_template.script += "\nimport os\n"
                for pvc, art in pvc_arts:
                    new_template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    new_template.script += \
                        "os.system('cp -r %s /tmp/mnt/%s')\n" % (
                            art.path, pvc.subpath)
                    new_template.pvcs.append(pvc)
            else:
                raise RuntimeError(
                    "Unsupported type of OPTemplate to mount PVC")

        if self.continue_on_num_success or self.continue_on_success_ratio is \
                not None:
            self.continue_on_failed = True
            if new_template is None:
                new_template = deepcopy(self.template)
                new_template.name = self.template.name + "-" + randstr()
            if (isinstance(new_template, ShellOPTemplate)):
                new_template.outputs.parameters["dflow_success_tag"] = \
                    OutputParameter(value_from_path="/tmp/success_tag",
                                    default="0")
                self.outputs.parameters["dflow_success_tag"] = \
                    OutputParameter(value_from_path="/tmp/success_tag",
                                    default="0")
                new_template.script += "\n"
                new_template.script += "echo 1 > /tmp/success_tag\n"
            elif (isinstance(new_template, PythonScriptOPTemplate)):
                new_template.outputs.parameters["dflow_success_tag"] = \
                    OutputParameter(value_from_path="/tmp/success_tag",
                                    default="0")
                self.outputs.parameters["dflow_success_tag"] = \
                    OutputParameter(value_from_path="/tmp/success_tag",
                                    default="0")
                new_template.script += "\n"
                new_template.script += "with open('/tmp/success_tag', 'w')"\
                    " as f:\n    f.write('1')\n"
            else:
                raise RuntimeError(
                    "Unsupported type of OPTemplate for "
                    "continue_on_num_success or continue_on_success_ratio")

        if self.continue_on_num_success is not None:
            self.check_step = self.__class__(
                name="%s-check-num-success" % self.name,
                template=CheckNumSuccess(
                    image=self.util_image,
                    image_pull_policy=self.util_image_pull_policy),
                parameters={
                    "success": self.outputs.parameters["dflow_success_tag"],
                    "threshold": self.continue_on_num_success
                }
            )
        elif self.continue_on_success_ratio is not None:
            self.check_step = self.__class__(
                name="%s-check-success-ratio" % self.name,
                template=CheckSuccessRatio(
                    image=self.util_image,
                    image_pull_policy=self.util_image_pull_policy),
                parameters={
                    "success": self.outputs.parameters["dflow_success_tag"],
                    "threshold": self.continue_on_success_ratio
                }
            )

        if new_template is not None:
            self.template = new_template

        if self.parallelism is not None:
            assert self.with_param is not None or self.with_sequence is not \
                None, "Only parallel step can be assigned with parallelism"
            from .dag import DAG
            from .steps import Steps
            from .task import Task
            if isinstance(self, Task):
                steps = DAG(name="%s-par-steps" % self.template.name,
                            parallelism=self.parallelism)
            else:
                steps = Steps(name="%s-par-steps" % self.template.name,
                              parallelism=self.parallelism)
            steps.inputs = deepcopy(self.template.inputs)
            for par in steps.inputs.parameters.values():
                par.path = None
            for art in steps.inputs.artifacts.values():
                art.path = None
            steps.outputs = deepcopy(self.template.outputs)
            for par in steps.outputs.parameters.values():
                par.value_from_path = None
            for art in steps.outputs.artifacts.values():
                art.path = None

            step = deepcopy(self)
            step.when = None
            for name in list(self.inputs.parameters.keys()):
                if name[:6] == "dflow_" and name[-9:] == "_sub_path" or \
                        name[:10] == "dflow_var_":
                    del steps.inputs.parameters[name]
                    del self.inputs.parameters[name]
                else:
                    step.set_parameters({name: steps.inputs.parameters[name]})
            for name, art in list(self.inputs.artifacts.items()):
                art.sub_path = None
                if isinstance(art.source, S3Artifact):
                    del steps.inputs.artifacts[name]
                    del self.inputs.artifacts[name]
                else:
                    step.set_artifacts({name: steps.inputs.artifacts[name]})
            for name in list(step.prepare_step.inputs.parameters.keys()):
                step.prepare_step.set_parameters({
                    name: steps.inputs.parameters[name]})
            for name, art in list(self.prepare_step.inputs.artifacts.items()):
                if not isinstance(art.source, S3Artifact):
                    step.prepare_step.set_artifacts({
                        name: steps.inputs.artifacts[name]})
            steps.add(step)
            for name, par in list(self.outputs.parameters.items()):
                if not par.save_as_artifact:
                    steps.outputs.parameters[name].value_from_parameter = \
                        step.outputs.parameters[name]
                else:
                    del steps.outputs.parameters[name]
                    del self.outputs.parameters[name]
            for name, art in list(self.outputs.artifacts.items()):
                if art.redirect is not None:
                    steps.outputs.artifacts[name]._from = \
                        step.outputs.artifacts[name]
                else:
                    del steps.outputs.artifacts[name]
                    del self.outputs.artifacts[name]

            for name in self.outputs.artifacts.keys():
                self.outputs.artifacts[name].redirect = None
            self.template = steps
            self.continue_on_num_success = None
            self.continue_on_success_ratio = None
            self.key = None
            self.executor = None
            self.use_resource = None
            self.prepare_step = None
            self.check_step = None

            if "dflow_key" in steps.inputs.parameters:
                fields = re.split("{{item[^}]*}}",
                                  self.inputs.parameters["dflow_key"].value)
                exprs = re.findall("{{item[^}]*}}",
                                   self.inputs.parameters["dflow_key"].value)
                for i in range(len(fields)):
                    steps.inputs.parameters["dflow_key_%s" % i] = \
                        InputParameter()
                del steps.inputs.parameters["dflow_key"]
                key = str(steps.inputs.parameters["dflow_key_0"])
                for i, expr in enumerate(exprs):
                    key += expr
                    key += str(steps.inputs.parameters["dflow_key_%s" % (i+1)])
                step.set_parameters({"dflow_key": key})
                for i, field in enumerate(fields):
                    self.inputs.parameters["dflow_key_%s" % i] = \
                        InputParameter(value=field)
                del self.inputs.parameters["dflow_key"]
            if self.with_param is not None:
                steps.inputs.parameters["dflow_with_param"] = InputParameter()
                step.with_param = steps.inputs.parameters["dflow_with_param"]
                self.inputs.parameters["dflow_with_param"] = InputParameter(
                    value=self.with_param)
                self.with_param = None
            if self.with_sequence is not None:
                if self.with_sequence.start is not None:
                    steps.inputs.parameters["dflow_sequence_start"] = \
                        InputParameter()
                    step.with_sequence.start = "{{=%s}}" % \
                        steps.inputs.parameters["dflow_sequence_start"].expr
                if self.with_sequence.end is not None:
                    steps.inputs.parameters["dflow_sequence_end"] = \
                        InputParameter()
                    step.with_sequence.end = "{{=%s}}" % \
                        steps.inputs.parameters["dflow_sequence_end"].expr
                if self.with_sequence.count is not None:
                    steps.inputs.parameters["dflow_sequence_count"] = \
                        InputParameter()
                    step.with_sequence.count = "{{=%s}}" % \
                        steps.inputs.parameters["dflow_sequence_count"].expr
                self.with_sequence = None

        if GLOBAL_CONTEXT.in_context:
            if not self.name.endswith('init-artifact'):
                GLOBAL_CONTEXT.current_workflow.add(self)
            else:
                if self.name.endswith('init-artifact-init-artifact'):
                    raise ValueError(
                        "Please don't name step as '***init-artifact'")

    def __repr__(self):
        return self.id

    def set_parameters(self, parameters):
        for k, v in parameters.items():
            # if a parameter is saved as artifact, the parameters it pass
            # value to or its value comes from must be saved as artifact
            # as well
            if isinstance(v, (InputParameter, OutputParameter)):
                if self.inputs.parameters[k].type is None and v.type is not \
                        None:
                    self.inputs.parameters[k].type = v.type
                if v.type is None and self.inputs.parameters[k].type is not \
                        None:
                    v.type = self.inputs.parameters[k].type

                if self.inputs.parameters[k].save_as_artifact:
                    v.save_as_artifact = True
                if v.save_as_artifact:
                    self.inputs.parameters[k].save_as_artifact = True

            if self.inputs.parameters[k].save_as_artifact and isinstance(v, (
                    InputParameter, OutputParameter, InputArtifact,
                    OutputArtifact)):
                self.inputs.parameters[k].source = v
                continue

            if v is None:
                self.inputs.parameters[k].value = "null"
            else:
                self.inputs.parameters[k].value = v

    def set_artifacts(self, artifacts):
        for k, v in artifacts.items():
            if v is None:
                del self.inputs.artifacts[k]
                self.template.inputs.artifacts[k].optional = True
            else:
                self.inputs.artifacts[k].source = v
                if config["save_path_as_parameter"]:
                    if isinstance(v, S3Artifact) and v.path_list is not None:
                        try:
                            path_list = catalog_of_artifact(v)
                            if path_list:
                                v.path_list = path_list
                        except Exception:
                            pass
                        self.inputs.parameters["dflow_%s_path_list" % k] = \
                            InputParameter(value=v.path_list)
                    elif isinstance(v, OutputArtifact) and v.step is not None \
                            and "dflow_%s_path_list" % v.name in \
                                v.step.outputs.parameters:
                        self.inputs.parameters["dflow_%s_path_list" % k] = \
                            InputParameter(
                            value=v.step.outputs.parameters[
                                "dflow_%s_path_list" % v.name])
                    elif isinstance(v, InputArtifact) and v.template is not \
                            None and "dflow_%s_path_list" % v.name in \
                            v.template.inputs.parameters:
                        self.inputs.parameters["dflow_%s_path_list" % k] = \
                            InputParameter(
                            value=v.template.inputs.parameters[
                                "dflow_%s_path_list" % v.name])

    def prepare_argo_arguments(self, context=None):
        self.argo_parameters = []
        self.argo_artifacts = []
        for par in self.inputs.parameters.values():
            if par.save_as_artifact:
                self.argo_artifacts.append(par.convert_to_argo())
            else:
                self.argo_parameters.append(par.convert_to_argo())

        for art in self.inputs.artifacts.values():
            if isinstance(art.source, PVC):
                pass
            elif art.source is None and art.optional:
                pass
            else:
                self.argo_artifacts.append(art.convert_to_argo())

        if isinstance(self.with_param, ArgoVar):
            self.with_param = "{{=%s}}" % self.with_param.expr
        elif self.with_param is not None and not isinstance(self.with_param,
                                                            str):
            self.with_param = jsonpickle.dumps(list(self.with_param))

        if context is not None:
            self.template = context.render(self.template)

        if self.executor is not None:
            assert isinstance(self.executor, Executor)
            self.template = self.executor.render(self.template)

        if self.use_resource is not None:
            self.template.resource = V1alpha1ResourceTemplate(
                action=self.use_resource.action,
                success_condition=self.use_resource.success_condition,
                failure_condition=self.use_resource.failure_condition,
                manifest=self.use_resource.get_manifest(self.template.command,
                                                        self.template.script))

    def convert_to_argo(self, context=None):
        logging.debug("handle step %s" % self.name)
        self.prepare_argo_arguments(context)
        return V1alpha1WorkflowStep(
            name=self.name, template=self.template.name,
            arguments=V1alpha1Arguments(
                parameters=self.argo_parameters,
                artifacts=self.argo_artifacts
            ), when=self.when, with_param=self.with_param,
            with_sequence=self.with_sequence,
            continue_on=V1alpha1ContinueOn(failed=self.continue_on_failed)
        )

    def run(self, context):
        self.phase = "Running"
        if self.executor is not None:
            assert isinstance(self.executor, Executor)
            self.template = self.executor.render(self.template)

        import os
        from copy import copy
        from .dag import DAG
        from .steps import Steps

        if self.when is not None:
            expr = render_expr(self.when, context)
            if not eval_bool_expr(expr):
                self.phase = "Skipped"
                return

        # source input parameters
        parameters = deepcopy(self.inputs.parameters)
        for name, par in parameters.items():
            value = par.value
            if isinstance(value, (InputParameter, OutputParameter)):
                par.value = get_var(value, context).value
            elif isinstance(value, str):
                par.value = render_expr(par.value, context)

        # source input artifacts
        for name, art in self.inputs.artifacts.items():
            if isinstance(art.source, (InputArtifact, OutputArtifact)):
                art.source = get_var(art.source, context)

        if isinstance(self.template, (Steps, DAG)):
            # shallow copy to avoid changing each step
            steps = copy(self.template)
            steps.inputs = deepcopy(self.template.inputs)

            # override default inputs with arguments
            for name, par in parameters.items():
                steps.inputs.parameters[name].value = par.value

            for name, art in self.inputs.artifacts.items():
                steps.inputs.artifacts[name].local_path = art.source.local_path

            steps.run()

            for name, par in self.outputs.parameters.items():
                if par.value_from_parameter is not None:
                    par.value = get_var(par.value_from_parameter, steps).value
                elif par.value_from_expression is not None:
                    _if = par.value_from_expression._if
                    _if = render_expr(_if, steps)
                    if eval_bool_expr(_if):
                        _then = par.value_from_expression._then
                        par.value = get_var(_then, steps).value
                    else:
                        _else = par.value_from_expression._else
                        par.value = get_var(_else, steps).value

            for name, art in self.outputs.artifacts.items():
                if art._from is not None:
                    art.local_path = get_var(art._from, steps).local_path
                elif art.from_expression is not None:
                    _if = art.from_expression._if
                    _if = render_expr(_if, steps)
                    if eval_bool_expr(_if):
                        _then = art.from_expression._then
                        art.local_path = get_var(_then, steps).local_path
                    else:
                        _else = art.from_expression._else
                        art.local_path = get_var(_else, steps).local_path

            self.phase = "Succeeded"
            return

        if self.with_param is not None or self.with_sequence is not None:
            if isinstance(self.with_param, (InputParameter, OutputParameter)):
                item_list = self.with_param.value
            elif isinstance(self.with_param, list):
                item_list = self.with_param
            elif self.with_sequence is not None:
                start = 0
                if self.with_sequence.start is not None:
                    start = self.with_sequence.start
                    if isinstance(start, (InputParameter, OutputParameter)):
                        start = start.value
                if self.with_sequence.count is not None:
                    count = self.with_sequence.count
                    if isinstance(count, (InputParameter, OutputParameter)):
                        count = count.value
                    sequence = list(range(start, start + count))
                if self.with_sequence.end is not None:
                    end = self.with_sequence.end
                    if isinstance(end, (InputParameter, OutputParameter)):
                        end = end.value
                    sequence = list(range(start, end + 1))
                if self.with_sequence.format is not None:
                    item_list = [self.with_sequence.format % i
                                 for i in sequence]
                else:
                    item_list = sequence
            else:
                raise RuntimeError("Not supported")

            procs = []
            self.parallel_steps = []
            assert isinstance(item_list, list)
            from multiprocessing import Process, Queue
            queue = Queue()
            for i, item in enumerate(item_list):
                ps = deepcopy(self)
                ps.phase = "Pending"
                self.parallel_steps.append(ps)
                proc = Process(target=ps.exec_with_queue,
                               args=(context, parameters, i, queue, item))
                proc.start()
                procs.append(proc)

            for i in range(len(item_list)):
                # TODO: if the process is killed, this will be blocked forever
                j, ps = queue.get()
                if ps is None:
                    self.parallel_steps[j].phase = "Failed"
                    if not self.continue_on_failed:
                        self.phase = "Failed"
                        raise RuntimeError("Step %s failed" %
                                           self.parallel_steps[j])
                else:
                    self.parallel_steps[j].outputs = deepcopy(ps.outputs)

            for name, par in self.outputs.parameters.items():
                par.value = []
                for ps in self.parallel_steps:
                    value = ps.outputs.parameters[name].value
                    if isinstance(value, str):
                        par.value.append(value)
                    else:
                        par.value.append(jsonpickle.loads(value))
            for name, art in self.outputs.artifacts.items():
                for save in self.template.outputs.artifacts[name].save:
                    if isinstance(save, S3Artifact):
                        key = render_script(save.key, parameters,
                                            context.workflow_id)
                        art.local_path = os.path.abspath(os.path.join("..",
                                                                      key))
            self.phase = "Succeeded"
        else:
            try:
                self.exec(context, parameters)
            except Exception:
                self.phase = "Failed"
                if not self.continue_on_failed:
                    raise RuntimeError("Step %s failed" % self)

    def run_with_queue(self, context, order, queue):
        try:
            self.run(context)
            queue.put((order, self))
        except Exception:
            import traceback
            traceback.print_exc()
            queue.put((order, None))

    def exec(self, context, parameters, item=None):
        """
        directory structure:
        step-xxxxx
        |- inputs
           |- parameters
           |- artifacts
        |- outputs
           |- parameters
           |- artifacts
        |- script
        |- workdir
        """
        self.phase = "Running"

        # render item
        if item is not None:
            for name, par in parameters.items():
                if isinstance(par.value, str):
                    par.value = render_item(par.value, item)

        import os
        import shutil
        cwd = os.getcwd()
        if "dflow_key" in parameters:
            step_id = parameters["dflow_key"].value
            stepdir = os.path.abspath(step_id)
            if os.path.exists(stepdir):
                # load parameters
                for name, par in self.outputs.parameters.items():
                    par_path = os.path.join(stepdir,
                                            "outputs/parameters/%s" % name)
                    with open(par_path, "r") as f:
                        if par.type is None or par.type == str:
                            par.value = f.read()
                        else:
                            par.value = jsonpickle.loads(f.read())

                # load artifacts
                for name, art in self.outputs.artifacts.items():
                    art_path = os.path.join(stepdir,
                                            "outputs/artifacts/%s" % name)
                    art.local_path = art_path

                os.chdir(cwd)
                self.phase = "Succeeded"
                return
        else:
            while True:
                step_id = self.name + "-" + randstr()
                stepdir = os.path.abspath(step_id)
                if not os.path.exists(stepdir):
                    os.makedirs(stepdir)
                    break

        workdir = os.path.join(stepdir, "workdir")
        os.makedirs(workdir, exist_ok=True)
        os.chdir(workdir)

        # render parameters
        os.makedirs(os.path.join(stepdir, "inputs/parameters"), exist_ok=True)
        for name, par in parameters.items():
            par_path = os.path.join(stepdir, "inputs/parameters/%s" % name)
            with open(par_path, "w") as f:
                f.write(par.value if isinstance(par.value, str)
                        else jsonpickle.dumps(par.value))

        # render artifacts
        os.makedirs(os.path.join(stepdir, "inputs/artifacts"), exist_ok=True)
        for name, art in self.inputs.artifacts.items():
            art_path = os.path.join(stepdir, "inputs/artifacts/%s" % name)
            if isinstance(art.source, (InputArtifact, OutputArtifact,
                                       LocalArtifact)):
                if art.sub_path is not None:
                    sub_path = art.sub_path
                    if item is not None:
                        sub_path = render_item(sub_path, item)
                    os.symlink(os.path.join(art.source.local_path, sub_path),
                               art_path)
                else:
                    os.symlink(art.source.local_path, art_path)
            elif isinstance(art.source, str):
                with open(art_path, "w") as f:
                    f.write(art.source)
            else:
                raise RuntimeError("Not supported: ", art.source)

            path = self.template.inputs.artifacts[name].path
            if hasattr(self.template, "tmp_root"):
                path = "%s/%s" % (workdir, path)
            path = render_script(path, parameters,
                                 context.workflow_id, step_id)
            os.makedirs(os.path.dirname(
                os.path.abspath(path)), exist_ok=True)
            backup(path)
            os.symlink(art_path, path)

        # clean output path
        for art in self.outputs.artifacts.values():
            path = art.path
            if hasattr(self.template, "tmp_root"):
                path = "%s/%s" % (workdir, path)
            backup(path)

        # render variables in the script
        script = self.template.script
        if hasattr(self.template, "tmp_root"):
            # do not modify self.template
            template = deepcopy(self.template)
            template.tmp_root = "%s/%s" % (workdir, template.tmp_root)
            template.render_script()
            if self.executor is not None:
                if hasattr(self.executor, "work_root"):
                    self.executor.work_root = "."
                template = self.executor.render(template)
            script = template.script
        script = render_script(script, parameters,
                               context.workflow_id, step_id)
        script_path = os.path.join(stepdir, "script")
        with open(script_path, "w") as f:
            f.write(script)
        cmd = " ".join(self.template.command) + " " + script_path
        ret_code = os.system(cmd)
        if ret_code != 0:
            raise RuntimeError("Run [%s] failed" % cmd)

        # save parameters
        os.makedirs(os.path.join(stepdir, "outputs/parameters"), exist_ok=True)
        for name, par in self.outputs.parameters.items():
            par_path = os.path.join(stepdir,
                                    "outputs/parameters/%s" % name)
            path = par.value_from_path
            if path is not None:
                if hasattr(self.template, "tmp_root"):
                    path = "%s/%s" % (workdir, path)
                with open(path, "r") as f:
                    if par.type is None or par.type == str:
                        par.value = f.read()
                    else:
                        par.value = jsonpickle.loads(f.read())
                os.symlink(path, par_path)
            elif hasattr(par, "value"):
                if isinstance(par.value, str):
                    par.value = render_script(
                        par.value, parameters, context.workflow_id,
                        step_id)
                    value = par.value
                else:
                    value = jsonpickle.dumps(par.value)
                with open(par_path, "w") as f:
                    f.write(value)

        # save artifacts
        os.makedirs(os.path.join(stepdir, "outputs/artifacts"), exist_ok=True)
        for name, art in self.outputs.artifacts.items():
            art_path = os.path.join(stepdir, "outputs/artifacts/%s" % name)
            path = art.path
            if hasattr(self.template, "tmp_root"):
                path = "%s/%s" % (workdir, path)
            os.symlink(path, art_path)
            art.local_path = art_path
            for save in self.template.outputs.artifacts[name].save:
                if isinstance(save, S3Artifact):
                    key = render_script(save.key, parameters,
                                        context.workflow_id, step_id)
                    save_path = os.path.join(cwd, "..", key)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    def link(src, dst):
                        try:
                            os.link(src, dst)
                        except Exception:
                            pass
                    shutil.copytree(art_path, save_path, copy_function=link,
                                    dirs_exist_ok=True)
                    art.local_path = save_path

        os.chdir(cwd)
        self.phase = "Succeeded"

    def exec_with_queue(self, context, parameters, order, queue, item=None):
        try:
            self.exec(context, parameters, item)
            queue.put((order, self))
        except Exception:
            import traceback
            traceback.print_exc()
            queue.put((order, None))


def render_item(expr, item):
    i = expr.find("{{item")
    while i >= 0:
        j = expr.find("}}", i+2)
        var = expr[i+2:j]
        fields = var.split(".")
        value = item
        for key in fields[1:]:
            value = value[key]
        value = value if isinstance(value, str) else jsonpickle.dumps(value)
        expr = expr[:i] + value.strip() + expr[j+2:]
        i = expr.find("{{item", i+1)
    return expr


def render_expr(expr, context):
    # render variables
    i = expr.find("{{")
    while i >= 0:
        j = expr.find("}}", i+2)
        var = get_var(expr[i:j+2], context)
        if var:
            value = var.value
            value = value if isinstance(value, str) else \
                jsonpickle.dumps(value)
            expr = expr[:i] + value.strip() + expr[j+2:]
        i = expr.find("{{", i+1)
    return expr


def get_var(expr, context):
    expr = str(expr)
    assert expr[:2] == "{{" and expr[-2:] == "}}", "Parse failed: %s" % expr
    fields = expr[2:-2].split(".")
    if fields[:2] == ["inputs", "parameters"]:
        name = fields[2]
        return context.inputs.parameters[name]
    elif fields[:2] == ["inputs", "artifacts"]:
        name = fields[2]
        return context.inputs.artifacts[name]
    elif fields[0] in ["steps", "tasks"] and \
            fields[2:4] == ["outputs", "parameters"]:
        step_name = fields[1]
        name = fields[4]
        for step in context:
            if isinstance(step, list):
                for ps in step:
                    if ps.name == step_name:
                        return ps.outputs.parameters[name]
            elif step.name == step_name:
                return step.outputs.parameters[name]
        raise RuntimeError("Parse failed: %s" % expr)
    elif fields[0] in ["steps", "tasks"] and \
            fields[2:4] == ["outputs", "artifacts"]:
        step_name = fields[1]
        name = fields[4]
        for step in context:
            if isinstance(step, list):
                for ps in step:
                    if ps.name == step_name:
                        return ps.outputs.artifacts[name]
            elif step.name == step_name:
                return step.outputs.artifacts[name]
        raise RuntimeError("Parse failed: %s" % expr)
    elif fields[0] == "item":
        return None  # ignore
    else:
        raise RuntimeError("Not supported: %s" % expr)


def eval_bool_expr(expr):
    # For the original evaluator in argo, please refer to
    # https://github.com/antonmedv/expr
    import os
    expr = expr.replace("<=", "-le")
    expr = expr.replace(">=", "-ge")
    expr = expr.replace("<", "-lt")
    expr = expr.replace(">", "-gt")
    result = os.popen(
        "sh -c 'if [[ %s ]]; then echo 1; else echo 0; fi'"
        % expr).read().strip()
    if result == "1":
        return True
    elif result == "0":
        return False
    else:
        raise RuntimeError("Evaluate expression failed: %s" % expr)


def render_script(script, parameters, workflow_id=None, step_id=None):
    if workflow_id is not None:
        script = script.replace("{{workflow.name}}", workflow_id)
    if step_id is not None:
        script = script.replace("{{pod.name}}", step_id)
    i = script.find("{{")
    while i >= 0:
        j = script.find("}}", i+2)
        var = script[i+2:j]
        fields = var.split(".")
        if fields[0] == "inputs" and fields[1] == "parameters":
            par = fields[2]
            value = parameters[par].value
            script = script[:i] + (value if isinstance(value, str)
                                   else jsonpickle.dumps(value)) + script[j+2:]
        else:
            raise RuntimeError("Not supported: %s" % var)
        i = script.find("{{", i+1)
    return script


def backup(path):
    import os
    import shutil
    cnt = 0
    bk = path
    while os.path.exists(bk) or os.path.islink(bk):
        cnt += 1
        bk = path + ".bk%s" % cnt
    if bk != path:
        shutil.move(path, bk)