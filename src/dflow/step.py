import json
import logging
import os
import re
import shlex
import shutil
import sys
import tarfile
import time
import uuid
from copy import copy, deepcopy
from typing import Any, Dict, List, Optional, Union

from .common import (CustomArtifact, HTTPArtifact, LocalArtifact, S3Artifact,
                     field_errmsg, field_regex, jsonpickle, key_errmsg,
                     key_regex)
from .config import config, s3_config
from .context_syntax import GLOBAL_CONTEXT
from .executor import Executor
from .io import (PVC, ArgoVar, Expression, InputArtifact, InputParameter,
                 InputParameters, OutputArtifact, OutputParameter,
                 if_expression, type_to_str)
from .op_template import (OPTemplate, PythonScriptOPTemplate, ScriptOPTemplate,
                          ShellOPTemplate)
from .python import Slices
from .resource import Resource
from .util_ops import CheckNumSuccess, CheckSuccessRatio, InitArtifactForSlices
from .utils import (ProcessPoolExecutor, catalog_of_artifact, copy_file,
                    download_s3, evalable_repr, flatten, force_link, get_key,
                    merge_dir, randstr, upload_artifact)

try:
    from argo.workflows.client import (V1alpha1Arguments, V1alpha1ContinueOn,
                                       V1alpha1ResourceTemplate, V1VolumeMount)

    from .client import (V1alpha1Sequence, V1alpha1LifecycleHook,
                         V1alpha1WorkflowStep)
except Exception:
    V1alpha1Sequence = object


uploaded_python_packages = []


class ArgoRange(ArgoVar):
    def __init__(self, end, start=0, step=1):
        self.end = end
        self.start = start
        self.step = step
        if isinstance(start, (InputParameter, OutputParameter)):
            start = "sprig.atoi(%s)" % start.expr
        if isinstance(step, (InputParameter, OutputParameter)):
            step = "sprig.atoi(%s)" % step.expr
        if isinstance(end, (InputParameter, OutputParameter)):
            end = "sprig.atoi(%s)" % end.expr
        super().__init__("toJson(sprig.untilStep(%s, %s, %s))" %
                         (start, end, step))


def argo_range(
        *args,
) -> ArgoVar:
    """
    Return a str representing a range of integer in Argo
    It receives 1-3 arguments, which is similar to the function `range` in
        Python
    Each argument can be Argo parameter
    """
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
    return ArgoRange(end, start, step)


class ArgoSequence:
    def __init__(self, count, start, end, format):
        self.count = count
        self.start = start
        self.end = end
        self.format = format

    @classmethod
    def from_dict(cls, d):
        if d is None:
            return None
        kwargs = {
            "count": d.get("count", None),
            "start": d.get("start", None),
            "end": d.get("end", None),
            "format": d.get("format", None),
        }
        return cls(**kwargs)

    def to_dict(self):
        return {
            "count": "{{=%s}}" % self.count.expr if isinstance(
                self.count, ArgoVar) else self.count,
            "start": "{{=%s}}" % self.start.expr if isinstance(
                self.start, ArgoVar) else self.start,
            "end": "{{=%s}}" % self.end.expr if isinstance(
                self.end, ArgoVar) else self.end,
            "format": self.format
        }

    def convert_to_argo(self):
        count = self.count
        start = self.start
        end = self.end
        if isinstance(count, ArgoVar):
            count = "{{=%s}}" % count.expr
        if isinstance(start, ArgoVar):
            start = "{{=%s}}" % start.expr
        if isinstance(end, ArgoVar):
            end = "{{=%s}}" % end.expr
        return V1alpha1Sequence(count=count, start=start, end=end,
                                format=self.format)

    def evalable_repr(self, imports):
        kwargs = {k: getattr(self, k)
                  for k in ["count", "start", "end", "format"]
                  if getattr(self, k) is not None}
        imports.add(("dflow", "argo_sequence"))
        return "argo_sequence(%s)" % ", ".join(["%s=%s" % (k, evalable_repr(
            v, imports)) for k, v in kwargs.items()])


def argo_sequence(
        count: Union[int, ArgoVar] = None,
        start: Union[int, ArgoVar] = None,
        end: Union[int, ArgoVar] = None,
        format: Optional[str] = None,
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
    return ArgoSequence(count=count, start=start, end=end, format=format)


class ArgoLen(ArgoVar):
    def __init__(self, param):
        self.param = param
        if isinstance(param, S3Artifact):
            try:
                path_list = catalog_of_artifact(param)
                if path_list:
                    param.path_list = path_list
            except Exception:
                pass
            super().__init__(str(len(param.path_list)))
        if isinstance(param, InputArtifact):
            assert config["save_path_as_parameter"]
            super().__init__("len(sprig.fromJson(%s))" %
                             param.get_path_list_parameter())
        elif isinstance(param, OutputArtifact):
            assert config["save_path_as_parameter"]
            super().__init__("len(sprig.fromJson(%s))" %
                             param.get_path_list_parameter())
        else:
            if isinstance(param, OutputParameter) and param.save_as_artifact:
                step = param.step
                step.template = step.template.deepcopy()
                step.template.outputs.parameters[param.name].save_both = True
                param.save_both = True
                super().__init__("len(sprig.fromJson(%s))" %
                                 param.expr_as_parameter())
            else:
                super().__init__("len(sprig.fromJson(%s))" % param.expr)


def argo_len(
        param: Union[ArgoVar, S3Artifact],
) -> ArgoVar:
    """
    Return the length of a list which is an Argo parameter

    Args:
        param: the Argo parameter which is a list
    """
    return ArgoLen(param)


class ArgoEnumerate(ArgoVar):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        param = list(kwargs.values())[0]
        if isinstance(param, ArgoVar):
            length = "len(sprig.fromJson(%s))" % param.expr
        else:
            length = len(param)
        values = ""
        for k, v in kwargs.items():
            values += ", '%s': jsonpath(%s, '$')[#]" % (
                k, v.expr if isinstance(v, ArgoVar)
                else shlex.quote(json.dumps(v)).replace("\\", "\\\\"))
        super().__init__(
            "toJson(map(sprig.untilStep(0, %s, 1), "
            "{ {'order': #%s} }))" % (length, values))


def argo_enumerate(
        *args, **kwargs,
) -> ArgoVar:
    """
    Return the enumeration of a list which is an Argo parameter

    Args:
        param: the Argo parameter which is a list
    """
    if len(args) == 1:
        kwargs["value"] = args[0]
    elif len(args) > 1:
        for i, arg in enumerate(args):
            kwargs["value" + str(i)] = arg
    return ArgoEnumerate(**kwargs)


class ArgoSum:
    def __init__(self, param):
        self.param = param
        self.expr = "sum(%s)" % param


def argo_sum(
        param: ArgoVar,
) -> ArgoSum:
    """
    Return the sum of a list of integers which is an Argo parameter

    Args:
        param: the Argo parameter which is a list of integers
    """
    return ArgoSum(param)


class ArgoConcat:
    def __init__(self, param):
        self.param = param
        self.expr = "concat(%s)" % param


def argo_concat(
        param: ArgoVar,
) -> ArgoConcat:
    """
    Return the concatenation of a list of lists which is an Argo parameter

    Args:
        param: the Argo parameter which is a list of lists
    """
    return ArgoConcat(param)


def upload_python_packages(python_packages):
    hit = list(filter(lambda x: x[0] == python_packages,
                      uploaded_python_packages))
    if len(hit) > 0:
        return hit[0][1]
    else:
        artifact = upload_artifact(python_packages)
        uploaded_python_packages.append((python_packages, artifact))
        return artifact


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
        continue_on_error: continue if the step meets error
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
        slices: override slices of OP template
    """

    def __init__(
            self,
            name: str,
            template: OPTemplate,
            parameters: Dict[str, Any] = None,
            artifacts: Dict[str, Optional[Union[
                S3Artifact, InputArtifact, OutputArtifact]]] = None,
            when: Optional[str] = None,
            with_param: Union[str, list,
                              InputParameter, OutputParameter] = None,
            continue_on_failed: bool = False,
            continue_on_error: bool = False,
            continue_on_num_success: Optional[int] = None,
            continue_on_success_ratio: Optional[float] = None,
            with_sequence: Optional[V1alpha1Sequence] = None,
            key: Optional[str] = None,
            executor: Optional[Executor] = None,
            use_resource: Optional[Resource] = None,
            util_image: Optional[str] = None,
            util_image_pull_policy: Optional[str] = None,
            util_command: Union[str, List[str]] = None,
            parallelism: Optional[int] = None,
            slices: Optional[Slices] = None,
            success_hook: Optional["HookStep"] = None,
            running_hook: Optional["HookStep"] = None,
            failure_hook: Optional["HookStep"] = None,
    ) -> None:
        assert field_regex.match(name), "Invalid step name '%s': %s" % (
            name, field_errmsg)
        self.name = name
        self.id = self.name
        self.template = template
        self.hooks = {}
        self.success_hook = success_hook
        self.running_hook = running_hook
        self.failure_hook = failure_hook
        self._with_param = with_param
        self.with_param = with_param
        if isinstance(self.with_param, str) and self.with_param.startswith(
                "{{=") and self.with_param.endswith("}}"):
            self.with_param = ArgoVar(self.with_param[3:-2])
        self._with_sequence = with_sequence
        self.with_sequence = with_sequence
        self._slices = slices or getattr(self.template, "slices", None)
        if slices is not None and slices.sub_path and all([isinstance(
                artifacts[n], list) for n in slices.input_artifact]):
            self.handle_sub_path_slices_of_artifact_list(slices, artifacts)
        elif getattr(self.template, "slices", None) is not None and \
            self.template.slices.sub_path and all([isinstance(
                artifacts[n], list) for n in
                self.template.slices.input_artifact]):
            self.template = self.template.copy()
            self.handle_sub_path_slices_of_artifact_list(self.template.slices,
                                                         artifacts)
            self.template.set_slices(self.template.slices)

        self.inputs = deepcopy(self.template.inputs)
        # We need not input artifact path for a step
        for art in self.inputs.artifacts.values():
            if isinstance(art.path, str) and "{{" in art.path:
                art.path = None
        self.outputs = deepcopy(self.template.outputs)
        self.inputs.set_step(self)
        self.outputs.set_step(self)
        self.continue_on_failed = continue_on_failed
        self.continue_on_error = continue_on_error
        self.continue_on_num_success = continue_on_num_success
        self.continue_on_success_ratio = continue_on_success_ratio
        self.check_step = None
        self.prepare_step = None

        if parameters is not None:
            self.set_parameters(parameters)

        if artifacts is not None:
            self.set_artifacts(artifacts)

        self.when = when
        if key is not None:
            clean_key = re.sub("{{[^}]*}}", "a", key)
            assert key_regex.match(clean_key), "Invalid key '%s': %s" % (
                key, key_errmsg)
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
            artifact = upload_python_packages(self.template.python_packages)
            self.set_artifacts({"dflow_python_packages": artifact})

        if self.key is not None:
            self.template.inputs.parameters["dflow_key"] = InputParameter(
                value="")
            self.inputs.parameters["dflow_key"] = InputParameter(
                value=str(self.key))

        if slices is not None:
            self.template = self.template.deepcopy()
            self.template.slices = slices
            self.template.add_slices(slices)
            for name, par in self.template.inputs.parameters.items():
                if name not in self.inputs.parameters:
                    self.inputs.parameters[name] = deepcopy(par)
            from .dag import DAG
            from .steps import Steps
            if isinstance(self.template, (DAG, Steps)):
                self.inputs.parameters["dflow_slice"] = InputParameter(
                    value=slices.slices)

        sum_var = None
        if isinstance(self.with_param, ArgoRange) and \
                isinstance(self.with_param.end, ArgoSum):
            sum_var = self.with_param.end.param

        if self.with_sequence is not None and \
                isinstance(self.with_sequence.count, ArgoSum):
            sum_var = self.with_sequence.count.param

        concat_var = None
        if isinstance(self.with_param, ArgoRange) and \
                isinstance(self.with_param.end, ArgoLen) and \
                isinstance(self.with_param.end.param, ArgoConcat):
            concat_var = self.with_param.end.param.param

        if self.with_sequence is not None and \
                isinstance(self.with_sequence.count, ArgoLen) and \
                isinstance(self.with_sequence.count.param, ArgoConcat):
            concat_var = self.with_sequence.count.param.param

        sliced_output_artifact = self.template.slices.output_artifact if \
            getattr(self.template, "slices", None) is not None else []

        sliced_input_artifact = self.template.slices.input_artifact if \
            getattr(self.template, "slices", None) is not None and \
            self.template.slices.sub_path else []

        auto_loop_artifacts = []
        if getattr(self.template, "slices", None) is not None and \
            not self.template.slices.sub_path and \
                self.with_param is None and self.with_sequence is None:
            if self.template.slices.input_parameter:
                name = self.template.slices.input_parameter[0]
                par = self.inputs.parameters[name]
                if hasattr(par, "value"):
                    if isinstance(par.value, str):
                        parameter_pattern = re.compile(
                            r"^{{(.*?)\.(.*?)\.(.*?)\.parameters\.(.*?)}}$")
                        match = parameter_pattern.match(par.value)
                        if match:
                            expr = "%s['%s'].%s.parameters['%s']" % (
                                match.group(1), match.group(2),
                                match.group(3), match.group(4))
                            self.with_param = argo_range(argo_len(ArgoVar(
                                expr)))
                        elif par.value.startswith("{{=") and \
                                par.value.endswith("}}"):
                            self.with_param = argo_range(argo_len(ArgoVar(
                                par.value[3:-2])))
                        else:
                            self.with_param = argo_range(len(json.loads(
                                par.value)))
                    elif hasattr(par.value, "__len__"):
                        self.with_param = argo_range(len(par.value))
                    else:
                        self.with_param = argo_range(argo_len(par.value))
                elif par.source is not None:
                    self.with_param = argo_range(argo_len(par.source))
            else:
                assert len(self.template.slices.input_artifact) > 0, "sliced "\
                    "input parameter or artifact must not be empty to infer "\
                    "with_param"
                auto_loop_artifacts = self.template.slices.input_artifact

        group_size = self.template.slices.group_size if getattr(
            self.template, "slices", None) is not None else None

        if sliced_output_artifact or sliced_input_artifact or \
            sum_var is not None or concat_var is not None or \
                auto_loop_artifacts:
            self.template = self.template.deepcopy()
            sequence_format = self.with_sequence.format \
                if self.with_sequence is not None else None
            init_template = InitArtifactForSlices(
                self.template, self.util_image, self.util_command,
                self.util_image_pull_policy, self.key, sliced_output_artifact,
                sliced_input_artifact, sum_var, concat_var,
                auto_loop_artifacts, group_size, sequence_format)
            if self.key is not None:
                self.template.inputs.parameters["dflow_group_key"] = \
                    InputParameter(value="")
                self.inputs.parameters["dflow_group_key"] = InputParameter(
                    value=re.sub("{{=?item.*}}", "group", str(self.key)))
                self.template.inputs.parameters["dflow_artifact_key"] = \
                    InputParameter(value="")
            else:
                self.template.inputs.parameters["dflow_artifact_key"] = \
                    InputParameter(value="")

            for name in sliced_output_artifact:
                def merge_step_output_artifact(art, parent, layer=0):
                    step = art.step
                    template = step.template
                    cur_key = "dflow_artifact_key_%s" % (layer + 1)
                    last_key = "dflow_artifact_key" if layer == 0 else \
                        "dflow_artifact_key_%s" % layer
                    if template is parent:
                        step.inputs.parameters[last_key] = InputParameter(
                            value="{{inputs.parameters.%s}}" % last_key)
                        return
                    template.inputs.parameters[cur_key] = InputParameter()
                    step.inputs.parameters[cur_key] = InputParameter(
                        value="{{inputs.parameters.%s}}" % last_key)
                    if step.prepare_step is not None and art.name in \
                            step.prepare_step.outputs.artifacts:
                        # for multi-merge, save output artifact of inner
                        # slices all together
                        step.prepare_step.template.inputs.parameters[
                            cur_key] = InputParameter()
                        step.prepare_step.inputs.parameters[cur_key] = \
                            InputParameter(value="{{inputs.parameters.%s}}"
                                           % last_key)
                        merge_output_artifact(
                            step.prepare_step.template.outputs.artifacts[
                                art.name], None, layer+1)
                    merge_output_artifact(template.outputs.artifacts[
                        art.name], template, layer+1)

                def merge_output_artifact(art, parent, layer=0):
                    if art._from is not None:
                        merge_step_output_artifact(
                            art._from, parent, layer)
                    elif art.from_expression is not None:
                        merge_step_output_artifact(
                            art.from_expression._then, parent, layer)
                        merge_step_output_artifact(
                            art.from_expression._else, parent, layer)
                    else:
                        key = "dflow_artifact_key" if layer == 0 else \
                            "dflow_artifact_key_%s" % layer
                        art.save.append(S3Artifact(
                            key="{{inputs.parameters.%s}}/%s"
                            % (key, name)))

                merge_output_artifact(
                    self.template.outputs.artifacts[name], self.template)

            if self.key is not None:
                group_key = re.sub("{{=?item.*}}", "group", str(self.key))
                self.prepare_step = self.__class__(
                    name="%s-init-artifact" % self.name,
                    template=init_template,
                    parameters={"dflow_group_key": group_key})
                self.inputs.parameters["dflow_artifact_key"] = InputParameter(
                    value=self.prepare_step.outputs.parameters[
                        "dflow_artifact_key"])
            else:
                self.prepare_step = self.__class__(
                    name="%s-init-artifact" % self.name,
                    template=init_template)
                self.inputs.parameters["dflow_artifact_key"] = InputParameter(
                    value=self.prepare_step.outputs.parameters[
                        "dflow_artifact_key"])

            if sliced_input_artifact:
                if self.key is not None:
                    self.prepare_step.inputs.parameters["dflow_key"].value = \
                        "%s-init-artifact" % group_key
                if group_size is not None:
                    for name in sliced_input_artifact:
                        self.prepare_step.set_artifacts({
                            name: self.inputs.artifacts[name].source})
                        self.inputs.artifacts[name].source = \
                            self.prepare_step.outputs.artifacts[name]
                        self.inputs.artifacts[name].sp = "group_{{item}}"
                    ngroups = self.prepare_step.outputs.parameters[
                        "dflow_ngroups"]
                    self.inputs.parameters["dflow_ngroups"].value = ngroups
                    if self.with_sequence is not None:
                        self.with_sequence = argo_sequence(
                            ngroups, format=self.with_sequence.format)
                    else:
                        self.with_param = argo_range(ngroups)
                else:
                    for name in sliced_input_artifact:
                        self.inputs.parameters[
                            "dflow_%s_sub_path" % name].value = \
                                "{{item.%s}}" % name
                        v = self.inputs.artifacts[name].source
                        if isinstance(v, S3Artifact):
                            self.prepare_step.set_artifacts({
                                name: v.sub_path(config["catalog_dir_name"])})
                            self.inputs.artifacts[name].source = \
                                v.sub_path("{{item.%s}}" % name)
                        elif v is not None:
                            self.prepare_step.set_artifacts({name: v})
                            self.inputs.artifacts[name].sp = "{{item.%s}}" % \
                                name
                        if self.with_sequence is not None:
                            for par in self.inputs.parameters.values():
                                if hasattr(par, "value") and isinstance(
                                        par.value, str):
                                    par.value = par.value.replace(
                                        "{{item}}", "{{item.order}}")
                            self.with_sequence = None
                        self.with_param = self.prepare_step.outputs.parameters[
                            "dflow_slices_path"]

            for name in sliced_output_artifact:
                self.outputs.artifacts[name].redirect = \
                    self.prepare_step.outputs.artifacts[name]

            if isinstance(self.with_param, ArgoRange) and \
                    isinstance(self.with_param.end, ArgoSum):
                name = sum_var.name
                self.prepare_step.inputs.parameters[name] = InputParameter(
                    value=str(sum_var))
                self.with_param = ArgoRange(
                    self.prepare_step.outputs.parameters["sum_%s" % name],
                    self.with_param.start,
                    self.with_param.step)

            if self.with_sequence is not None and \
                    isinstance(self.with_sequence.count, ArgoSum):
                name = sum_var.name
                self.prepare_step.inputs.parameters[name] = InputParameter(
                    value=str(sum_var))
                self.with_sequence = argo_sequence(
                    self.prepare_step.outputs.parameters["sum_%s" % name],
                    self.with_sequence.start, self.with_sequence.end,
                    self.with_sequence.format)

            if isinstance(self.with_param, ArgoRange) and \
                    isinstance(self.with_param.end, ArgoLen) and \
                    isinstance(self.with_param.end.param, ArgoConcat):
                name = concat_var.name
                self.prepare_step.inputs.parameters[name] = InputParameter(
                    value=str(concat_var))
                self.with_param = ArgoRange(
                    argo_len(self.prepare_step.outputs.parameters[
                        "concat_%s" % name]),
                    self.with_param.start,
                    self.with_param.step)

            if self.with_sequence is not None and \
                    isinstance(self.with_sequence.count, ArgoLen) and \
                    isinstance(self.with_sequence.count.param, ArgoConcat):
                name = concat_var.name
                self.prepare_step.inputs.parameters[name] = InputParameter(
                    value=str(concat_var))
                self.with_sequence = argo_sequence(
                    argo_len(self.prepare_step.outputs.parameters[
                        "concat_%s" % name]),
                    self.with_sequence.start, self.with_sequence.end,
                    self.with_sequence.format)

            if auto_loop_artifacts:
                for name in self.inputs.artifacts:
                    if name in auto_loop_artifacts or (name.startswith(
                            "dflow_") and name[6:name.rfind("_")] in
                            auto_loop_artifacts):
                        self.prepare_step.set_artifacts({
                            name: self.inputs.artifacts[name].source})
                self.with_param = argo_range(
                    self.prepare_step.outputs.parameters["dflow_nslices"])

        if getattr(self.template, "slices", None) is not None and \
            self.template.slices.group_size is not None and \
                not self.template.slices.sub_path:
            self.template = self.template.deepcopy()
            group_size = self.template.slices.group_size
            self.template.inputs.parameters["dflow_nslices"] = InputParameter()
            if self.template.slices.shuffle:
                self.template.pre_script += "import random\n"
                self.template.pre_script += "random.seed(%s)\n" % \
                    self.template.slices.random_seed
                # pre script is formatted
                self.template.pre_script += "shuffled = "\
                    "list(range({{{{inputs.parameters.dflow_nslices}}}}))\n"
                self.template.pre_script += "random.shuffle(shuffled)\n"
                self.template.pre_script += "random.seed()\n"  # unset seed
            if isinstance(self.with_param, ArgoRange):
                self.template.inputs.parameters["dflow_range_end"] = \
                    InputParameter()
                self.inputs.parameters["dflow_range_end"] = \
                    InputParameter(value=self.with_param.end)
                self.template.inputs.parameters["dflow_range_start"] = \
                    InputParameter()
                self.inputs.parameters["dflow_range_start"] = \
                    InputParameter(value=self.with_param.start)
                self.template.inputs.parameters["dflow_range_step"] = \
                    InputParameter()
                self.inputs.parameters["dflow_range_step"] = \
                    InputParameter(value=self.with_param.step)
                nslices = argo_len(self.with_param)
                old_slices = self.template.slices.slices
                self.template.slices.slices = \
                    "[range({{inputs.parameters.dflow_range_start}}, "\
                    "{{inputs.parameters.dflow_range_end}}, "\
                    "{{inputs.parameters.dflow_range_step}})"\
                    "[%s] for i in range({{item}}*%s, min(({{item}}+1)*%s"\
                    ", {{inputs.parameters.dflow_nslices}}))]" % (
                        old_slices.replace("{{item}}", "shuffled[i]"
                                           if self.template.slices.shuffle
                                           else "i"), group_size, group_size)
                # re-render the script
                self.template.set_slices(self.template.slices)
                self.with_param = argo_range(if_expression(
                    "%s %% %s > 0" % (nslices, group_size),
                    "sprig.int(%s/%s) + 1" % (nslices, group_size),
                    "sprig.int(%s/%s)" % (nslices, group_size)))
            elif self.with_param is not None:
                self.template.inputs.parameters["dflow_with_param"] = \
                    InputParameter()
                self.inputs.parameters["dflow_with_param"] = \
                    InputParameter(value=self.with_param)
                if hasattr(self.with_param, "__len__"):
                    nslices = len(self.with_param)
                else:
                    nslices = argo_len(self.with_param)
                old_slices = self.template.slices.slices
                self.template.slices.slices = \
                    "[jsonpickle.loads(r'''{{inputs.parameters.dflow_with_par"\
                    "am}}''')[%s] for i in range({{item}}*%s, min(({{item}}+1"\
                    ")*%s, {{inputs.parameters.dflow_nslices}}))]" % (
                        old_slices.replace("{{item}}", "shuffled[i]"
                                           if self.template.slices.shuffle
                                           else "i"), group_size, group_size)
                # re-render the script
                self.template.set_slices(self.template.slices)
                self.with_param = argo_range(if_expression(
                    "%s %% %s > 0" % (nslices, group_size),
                    "sprig.int(%s/%s) + 1" % (nslices, group_size),
                    "sprig.int(%s/%s)" % (nslices, group_size)))
            if self.with_sequence is not None:
                self.template.inputs.parameters["dflow_sequence_start"] = \
                    InputParameter()
                self.template.inputs.parameters["dflow_sequence_end"] = \
                    InputParameter()
                self.template.inputs.parameters["dflow_sequence_count"] = \
                    InputParameter()
                start = self.with_sequence.start
                if start is None:
                    start = 0
                end = self.with_sequence.end
                count = self.with_sequence.count
                format = self.with_sequence.format
                self.inputs.parameters["dflow_sequence_start"] = \
                    InputParameter(value=start)
                self.inputs.parameters["dflow_sequence_end"] = \
                    InputParameter(value=end)
                self.inputs.parameters["dflow_sequence_count"] = \
                    InputParameter(value=count)
                if count is not None:
                    nslices = count
                else:
                    nslices = if_expression(
                        "%s > %s" % (end, start),
                        "%s + 1 - %s" % (end, start),
                        "%s + 1 - %s" % (start, end))
                old_slices = self.template.slices.slices
                self.template.slices.slices = \
                    "[[%s for j in (range(int('{{inputs.parameters."\
                    "dflow_sequence_start}}'), int('{{inputs.parameters."\
                    "dflow_sequence_start}}') + int('{{inputs.parameters."\
                    "dflow_sequence_count}}') + 1) if '{{inputs.parameters."\
                    "dflow_sequence_count}}' != 'null' else range(int('{{"\
                    "inputs.parameters.dflow_sequence_start}}'), int('{{"\
                    "inputs.parameters.dflow_sequence_end}}') + 1) if int('{{"\
                    "inputs.parameters.dflow_sequence_end}}') > int('{{"\
                    "inputs.parameters.dflow_sequence_start}}') else range("\
                    "int('{{inputs.parameters.dflow_sequence_start}}'), "\
                    "int('{{inputs.parameters.dflow_sequence_end}}') - 1, -1)"\
                    ")][%s] for i in range(int('{{item}}')*%s, min((int('{{"\
                    "item}}')+1)*%s, {{inputs.parameters.dflow_nslices}}))]"\
                    % (old_slices.replace(
                        "'{{item}}'", "('%s' %% j)" % format)
                        if format is not None
                        else old_slices.replace("{{item}}", "j"),
                        "shuffled[i]" if self.template.slices.shuffle else "i",
                        group_size, group_size)
                # re-render the script
                self.template.set_slices(self.template.slices)
                self.with_sequence = argo_sequence(
                    count=if_expression(
                        "%s %% %s > 0" % (nslices, group_size),
                        "sprig.int(%s/%s) + 1" % (nslices, group_size),
                        "sprig.int(%s/%s)" % (nslices, group_size)),
                    format=format)

            self.inputs.parameters["dflow_nslices"] = InputParameter(
                value=nslices)

        if config["register_tasks"] and hasattr(self.template, "slices") and \
                self.template.slices and \
                self.template.slices.register_first_only:
            self.template = self.template.deepcopy()
            if self.with_param is not None:
                if isinstance(self.with_param, ArgoVar):
                    par = self.with_param.expr
                else:
                    par = self.with_param
                first = "jsonpath(%s, '$[0]')" % par
                self.inputs.parameters["dflow_first"] = InputParameter(
                    value="{{=string(%s) == %s ? %s : toJson(%s)}}" %
                    (first, first, first, first))
            elif self.with_sequence is not None:
                if self.with_sequence.start is not None:
                    first = self.with_sequence.start
                else:
                    first = 0
                self.inputs.parameters["dflow_first"] = InputParameter(
                    value=first)
                if self.with_sequence.format is not None:
                    self.template.first_var = "'" + self.with_sequence.format \
                        + "' % {{inputs.parameters.dflow_first}}"
                    self.template.render_script()

        pvc_arts = []
        for art in self.inputs.artifacts.values():
            if isinstance(art.source, PVC):
                pvc_arts.append((art.source, art))

        if len(pvc_arts) > 0:
            self.template = self.template.deepcopy()
            if (isinstance(self.template, ShellOPTemplate)):
                for pvc, art in pvc_arts:
                    del self.template.inputs.artifacts[art.name]
                    self.template.script = "ln -s /tmp/mnt/%s %s\n" % (
                        pvc.subpath, art.path) + self.template.script
                    self.template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    self.template.pvcs.append(pvc)
            elif (isinstance(self.template, PythonScriptOPTemplate)):
                for pvc, art in pvc_arts:
                    del self.template.inputs.artifacts[art.name]
                    self.template.script = \
                        "os.system('ln -s /tmp/mnt/%s %s')\n" % (
                            pvc.subpath, art.path) + self.template.script
                    self.template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    self.template.pvcs.append(pvc)
                self.template.script = "import os\n" + self.template.script
            else:
                raise RuntimeError(
                    "Unsupported type of OPTemplate to mount PVC")

        pvc_arts = []
        for art in self.outputs.artifacts.values():
            for save in art.save:
                if isinstance(save, PVC):
                    pvc_arts.append((save, art))

        if len(pvc_arts) > 0:
            self.template = self.template.deepcopy()
            if (isinstance(self.template, ShellOPTemplate)):
                self.template.script += "\n"
                for pvc, art in pvc_arts:
                    self.template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    self.template.script += "cp -r %s /tmp/mnt/%s\n" % (
                        art.path, pvc.subpath)
                    self.template.pvcs.append(pvc)
            elif (isinstance(self.template, PythonScriptOPTemplate)):
                self.template.script += "\nimport os\n"
                for pvc, art in pvc_arts:
                    self.template.mounts.append(V1VolumeMount(
                        name=pvc.name, mount_path="/tmp/mnt"))
                    self.template.script += \
                        "os.system('cp -r %s /tmp/mnt/%s')\n" % (
                            art.path, pvc.subpath)
                    self.template.pvcs.append(pvc)
            else:
                raise RuntimeError(
                    "Unsupported type of OPTemplate to mount PVC")

        if self.continue_on_num_success or self.continue_on_success_ratio is \
                not None:
            self.continue_on_failed = True
            self.template = self.template.deepcopy()

            def add_success_tag(templ):
                from .dag import DAG
                from .steps import Steps
                if isinstance(templ, ScriptOPTemplate):
                    templ.outputs.parameters["dflow_success_tag"] = \
                        OutputParameter(
                            value_from_path="/tmp/outputs/success_tag",
                            default="0")
                    from .python import PythonOPTemplate
                    if isinstance(templ, PythonOPTemplate):
                        templ.success_tag = True
                        templ.render_script()
                    elif isinstance(templ, ShellOPTemplate):
                        templ.script += "\necho 1 > /tmp/outputs/success_tag\n"
                    elif isinstance(templ, PythonScriptOPTemplate):
                        templ.script += "\nwith open('/tmp/outputs"\
                            "/success_tag', 'w') as f:\n    f.write('1')\n"
                elif isinstance(templ, (Steps, DAG)):
                    templ.outputs.parameters["dflow_success_tag"] = \
                        OutputParameter(
                            value_from_parameter="nonexist", default="1")

            add_success_tag(self.template)
            self.outputs.parameters["dflow_success_tag"] = deepcopy(
                self.template.outputs.parameters["dflow_success_tag"])

        if self.continue_on_num_success is not None:
            self.check_step = self.__class__(
                name="%s-check-num-success" % self.name,
                template=CheckNumSuccess(
                    name="%s-check-num-success" % self.template.name,
                    image=self.util_image,
                    image_pull_policy=self.util_image_pull_policy),
                parameters={
                    "success": self.outputs.parameters["dflow_success_tag"],
                    "threshold": self.continue_on_num_success
                }
            )
        elif self.continue_on_success_ratio is not None:
            if "dflow_nslices" in self.inputs.parameters:
                total = self.inputs.parameters["dflow_nslices"].value
            elif self.with_param is not None:
                if hasattr(self.with_param, "__len__"):
                    total = len(self.with_param)
                else:
                    total = argo_len(self.with_param)
            elif self.with_sequence is not None:
                if self.with_sequence.count is not None:
                    count = self.with_sequence.count
                    total = count
                start = 0
                if self.with_sequence.start is not None:
                    start = self.with_sequence.start
                if self.with_sequence.end is not None:
                    end = self.with_sequence.end
                    total = if_expression(
                        "%s > %s" % (end, start),
                        "%s + 1 - %s" % (end, start),
                        "%s + 1 - %s" % (start, end))
            self.check_step = self.__class__(
                name="%s-check-success-ratio" % self.name,
                template=CheckSuccessRatio(
                    name="%s-check-success-ratio" % self.template.name,
                    image=self.util_image,
                    image_pull_policy=self.util_image_pull_policy),
                parameters={
                    "success": self.outputs.parameters["dflow_success_tag"],
                    "total": total,
                    "threshold": self.continue_on_success_ratio
                }
            )

        if hasattr(self.executor, "modify_step"):
            self.executor.modify_step(self)

        if GLOBAL_CONTEXT.in_context:
            if not self.name.endswith('init-artifact'):
                GLOBAL_CONTEXT.current_workflow.add(self)
            else:
                if self.name.endswith('init-artifact-init-artifact'):
                    raise ValueError(
                        "Please don't name step as '***init-artifact'")

    @classmethod
    def from_dict(cls, d, templates):
        kwargs = {
            "name": d["name"],
            "template": templates[d["template"]],
            "parameters": {par["name"]: par["value"] for par in
                           d.get("arguments", {}).get("parameters", [])},
            "artifacts": {},
            "when": d.get("when", None),
            "with_param": d.get("withParam", None) or d.get("withItems", None),
            "continue_on_failed": d.get("continueOn", {}).get("failed", False),
            "continue_on_error": d.get("continueOn", {}).get("error", False),
            "with_sequence": ArgoSequence.from_dict(d.get("withSequence",
                                                          None)),
            "key": d.get("arguments", {}).get("parameters", {})
        }
        for art in d.get("arguments", {}).get("artifacts", {}):
            name = art["name"]
            if "from" in art:
                kwargs["artifacts"][name] = art["from"]
                if "subPath" in art:
                    kwargs["artifacts"][name] += "/" + art["subPath"]
            elif "s3" in art:
                kwargs["artifacts"][name] = S3Artifact(key=art["s3"]["key"],
                                                       debug_s3=True)
                if "subPath" in art:
                    kwargs["artifacts"][name] = kwargs["artifacts"][
                        name].sub_path(art["subPath"])
            elif "oss" in art:
                kwargs["artifacts"][name] = S3Artifact(
                    key=art["oss"]["key"], debug_s3=True)
                if "subPath" in art:
                    kwargs["artifacts"][name] = kwargs["artifacts"][
                        name].sub_path(art["subPath"])
            elif "http" in art:
                kwargs["artifacts"][name] = HTTPArtifact(
                    url=art["http"]["url"])
            elif "local" in art:
                kwargs["artifacts"][name] = LocalArtifact(
                    local_path=art["local"]["path"])
        kwargs["key"] = kwargs["parameters"].get("dflow_key", None)
        return cls(**kwargs)

    def __repr__(self):
        return self.id

    @property
    def expr(self):
        return "steps['%s']" % self.id

    def handle_sub_path_slices_of_artifact_list(self, slices, artifacts):
        n = len(artifacts[slices.input_artifact[0]])
        param = {}
        for name in slices.input_artifact:
            assert len(artifacts[name]) == n
            if all([isinstance(art, S3Artifact)
                    for art in artifacts[name]]):
                param[name] = [art.key[len(s3_config["prefix"]):]
                               if art.key.startswith(s3_config["prefix"])
                               else art.key for art in artifacts[name]]
                artifacts[name] = S3Artifact(key="{{item.%s}}" % name)
            elif all(isinstance(art, CustomArtifact)
                     for art in artifacts[name]):
                param[name] = [art.get_urn() for art in artifacts[name]]
                artifacts[name] = deepcopy(artifacts[name][0])
                artifacts[name].redirect = "{{item.%s}}" % name
        if isinstance(self.with_param, ArgoEnumerate):
            self.with_param = argo_enumerate(**self.with_param.kwargs, **param)
        else:
            self.with_param = argo_enumerate(
                **getattr(self.with_param, "kwargs", {}), **param)
        slices.slices = "{{item.order}}"
        slices.sub_path = False
        slices.input_artifact = []

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
                    if not v.save_as_artifact and v.step is not None:
                        raise TypeError("%s is big parameter, but %s is not"
                                        " big parameter" % (
                                            self.inputs.parameters[k], v))
                    v.save_as_artifact = True
                if v.save_as_artifact:
                    if not self.inputs.parameters[k].save_as_artifact and \
                            v.step is not None:
                        raise TypeError("%s is big parameter, but %s is not"
                                        " big parameter" % (
                                            v, self.inputs.parameters[k]))
                    self.inputs.parameters[k].save_as_artifact = True

            if self.inputs.parameters[k].save_as_artifact and isinstance(v, (
                    InputParameter, OutputParameter, InputArtifact,
                    OutputArtifact)):
                self.inputs.parameters[k].source = v
                continue

            self.inputs.parameters[k].value = v

    def set_artifacts(self, artifacts):
        for k, v in artifacts.items():
            if v is None:
                del self.inputs.artifacts[k]
                self.template.inputs.artifacts[k].optional = True
            elif isinstance(v, CustomArtifact):
                self.inputs.artifacts[k].source = v
                self.inputs.artifacts[k].save_as_parameter = True
                self.template = self.template.copy()
                self.template.inputs.artifacts[k].save_as_parameter = True
                from .python import PythonOPTemplate
                if isinstance(self.template, PythonOPTemplate):
                    self.template = v.render(self.template, k)
                from .dag import DAG
                from .steps import Steps
                if isinstance(self.template, (Steps, DAG)):
                    for step in sum([s if isinstance(s, list) else [s]
                                     for s in self.template], []):
                        for name, art in step.inputs.artifacts.items():
                            if art.source is self.template.inputs.artifacts[k]\
                                or getattr(art.source, "parent", None) is \
                                    self.template.inputs.artifacts[k]:
                                source_bk = art.source
                                # for sub_path object
                                art.source.save_as_parameter = True
                                step.set_artifacts({name: v})
                                art.source = source_bk
            elif isinstance(v, (list, tuple)):
                self.template = self.template.copy()
                slices = []
                for i, a in enumerate(v):
                    vn = "dflow_%s_%s" % (k, i)
                    self.template.inputs.artifacts[vn] = deepcopy(
                        self.template.inputs.artifacts[k])
                    self.inputs.artifacts[vn] = deepcopy(
                        self.template.inputs.artifacts[vn])
                    if hasattr(a, "slice") and a.slice is not None:
                        slices.append(a.slice)
                    else:
                        slices.append(None)
                from .dag import DAG
                from .steps import Steps
                if isinstance(self.template, (Steps, DAG)):
                    for step in sum([s if isinstance(s, list) else [s]
                                     for s in self.template], []):
                        for name, art in list(step.inputs.artifacts.items()):
                            if art.source is self.template.inputs.artifacts[k]\
                                or getattr(art.source, "parent", None) is \
                                    self.template.inputs.artifacts[k]:
                                artifact = []
                                for i, s in enumerate(slices):
                                    source = self.template.inputs.artifacts[
                                        "dflow_%s_%s" % (k, i)]
                                    s2 = getattr(art.source, "slice", None)
                                    if s is not None and s2 is not None:
                                        artifact.append(
                                            source["%s.%s" % (s, s2)])
                                    elif s is not None:
                                        artifact.append(source[s])
                                    elif s2 is not None:
                                        artifact.append(source[s2])
                                    else:
                                        artifact.append(source)
                                step.set_artifacts({name: artifact})
                else:
                    for i, a in enumerate(v):
                        vn = "dflow_%s_%s" % (k, i)
                        self.template.inputs.artifacts[vn].path = \
                            "%s/inputs/artifacts/%s" % (self.template.tmp_root,
                                                        vn)
                    if any(map(lambda x: x is not None, slices)):
                        self.template.input_artifact_prefix[k] = slices
                    self.template.n_parts[k] = len(v)
                    self.template.render_script()
                for i, a in enumerate(v):
                    vn = "dflow_%s_%s" % (k, i)
                    self.set_artifacts({vn: a})
                del self.template.inputs.artifacts[k]
                del self.inputs.artifacts[k]
            elif isinstance(v, dict):
                self.template = self.template.copy()
                slices = {}
                flat_v = flatten(v)
                for i, a in flat_v.items():
                    vn = "dflow_%s_%s" % (k, i)
                    self.template.inputs.artifacts[vn] = deepcopy(
                        self.template.inputs.artifacts[k])
                    self.inputs.artifacts[vn] = deepcopy(
                        self.template.inputs.artifacts[vn])
                    if hasattr(a, "slice") and a.slice is not None:
                        slices[i] = a.slice
                    else:
                        slices[i] = None
                from .dag import DAG
                from .steps import Steps
                if isinstance(self.template, (Steps, DAG)):
                    for step in sum([s if isinstance(s, list) else [s]
                                     for s in self.template], []):
                        for name, art in list(step.inputs.artifacts.items()):
                            if art.source is self.template.inputs.artifacts[k]\
                                or getattr(art.source, "parent", None) is \
                                    self.template.inputs.artifacts[k]:
                                artifact = {}
                                for i, s in slices.items():
                                    source = self.template.inputs.artifacts[
                                        "dflow_%s_%s" % (k, i)]
                                    s2 = getattr(art.source, "slice", None)
                                    if s is not None and s2 is not None:
                                        artifact[i] = source["%s.%s" % (s, s2)]
                                    elif s is not None:
                                        artifact[i] = source[s]
                                    elif s2 is not None:
                                        artifact[i] = source[s2]
                                    else:
                                        artifact[i] = source
                                step.set_artifacts({name: artifact})
                else:
                    for i, a in flat_v.items():
                        vn = "dflow_%s_%s" % (k, i)
                        self.template.inputs.artifacts[vn].path = \
                            "%s/inputs/artifacts/%s" % (self.template.tmp_root,
                                                        vn)
                    if any(map(lambda x: x is not None, slices.values())):
                        self.template.input_artifact_prefix[k] = slices
                    self.template.keys_of_parts[k] = list(v.keys())
                    self.template.render_script()
                for i, a in flat_v.items():
                    vn = "dflow_%s_%s" % (k, i)
                    self.set_artifacts({vn: a})
                del self.template.inputs.artifacts[k]
                del self.inputs.artifacts[k]
            else:
                self.inputs.artifacts[k].source = v
                if isinstance(v, str) and "}}/" in v:
                    i = v.find("}}/")
                    self.inputs.artifacts[k].source = v[:i+2]
                    self.inputs.artifacts[k].sp = v[i+3:]
                if getattr(v, "slice", None) is not None:
                    self.template = self.template.copy()
                    if isinstance(v.slice, (InputParameter, OutputParameter)):
                        self.template.inputs.parameters[
                            "dflow_%s" % v.slice.name] = InputParameter()
                        self.inputs.parameters["dflow_%s" % v.slice.name] = \
                            InputParameter(value=v.slice)
                        v.slice = "{{inputs.parameters.dflow_%s}}" % \
                            v.slice.name
                    from .dag import DAG
                    from .steps import Steps
                    if isinstance(self.template, (Steps, DAG)):
                        for step in sum([s if isinstance(s, list) else [s]
                                         for s in self.template], []):
                            for name, art in step.inputs.artifacts.items():
                                if art.source is \
                                        self.template.inputs.artifacts[k] or \
                                        getattr(art.source, "parent", None) is\
                                        self.template.inputs.artifacts[k]:
                                    if getattr(art.source, "slice", None) \
                                            is not None:
                                        slice = "%s.%s" % (v.slice,
                                                           art.source.slice)
                                    else:
                                        slice = v.slice
                                    step.set_artifacts({
                                        name: self.template.inputs.artifacts[
                                            k][slice]})
                    else:
                        self.template.input_artifact_prefix[k] = v.slice \
                            if isinstance(v.slice, int) else "'%s'" % v.slice
                        self.template.render_script()
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
                if config["register_tasks"] and k[:6] != "dflow_":
                    if isinstance(v, S3Artifact):
                        self.inputs.parameters["dflow_%s_urn" % k] = \
                            InputParameter(value=v.urn)
                    elif isinstance(v, OutputArtifact) and v.step is not None \
                            and "dflow_%s_urn" % v.name in \
                                v.step.outputs.parameters:
                        self.inputs.parameters["dflow_%s_urn" % k] = \
                            InputParameter(
                            value=v.step.outputs.parameters[
                                "dflow_%s_urn" % v.name])
                    elif isinstance(v, InputArtifact) and v.template is not \
                        None and "dflow_%s_urn" % v.name in \
                            v.template.inputs.parameters:
                        self.inputs.parameters["dflow_%s_urn" % k] = \
                            InputParameter(
                            value=v.template.inputs.parameters[
                                "dflow_%s_urn" % v.name])

    def render_by_executor(self, context=None):
        if self.executor is not None:
            assert isinstance(self.executor, Executor)
            self.template = self.executor.render(self.template)
            if hasattr(self.executor, "merge_sliced_step") and \
                    self.executor.merge_sliced_step:
                self.inputs.parameters["dflow_with_param"] = \
                    InputParameter(value="")
                self.inputs.parameters["dflow_sequence_start"] = \
                    InputParameter(value=0)
                self.inputs.parameters["dflow_sequence_end"] = \
                    InputParameter(value=None)
                self.inputs.parameters["dflow_sequence_count"] = \
                    InputParameter(value=None)
                self.inputs.parameters["dflow_sequence_format"] = \
                    InputParameter(value="")
                key = "0"
                if self.with_param is not None:
                    self.inputs.parameters["dflow_with_param"].value = \
                        self.with_param
                    self.with_param = None
                if self.with_sequence is not None:
                    start = self.with_sequence.start
                    if start is None:
                        start = 0
                    end = self.with_sequence.end
                    count = self.with_sequence.count
                    format = self.with_sequence.format
                    self.inputs.parameters["dflow_sequence_start"].value = \
                        start
                    self.inputs.parameters["dflow_sequence_end"].value = end
                    self.inputs.parameters["dflow_sequence_count"].value = \
                        count
                    self.inputs.parameters["dflow_sequence_format"].value = \
                        format
                    self.with_sequence = None
                    if format is not None:
                        key = format % 0
                if self.key is not None:
                    self.inputs.parameters["dflow_key"] = InputParameter(
                        value=str(self.key).replace("{{item}}", key))
        elif context is not None:
            self.template = context.render(self.template)

    def prepare_argo_arguments(self, context=None):
        if isinstance(self.with_param, ArgoVar):
            self.with_param = "{{=%s}}" % self.with_param.expr
        elif self.with_param is not None and not isinstance(self.with_param,
                                                            str):
            self.with_param = jsonpickle.dumps(list(self.with_param))

        self.render_by_executor(context)

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
            elif art.save_as_parameter:
                self.argo_parameters.append(art.convert_to_argo())
            else:
                self.argo_artifacts.append(art.convert_to_argo())

        if self.use_resource is not None:
            self.template.resource = V1alpha1ResourceTemplate(
                action=self.use_resource.action,
                success_condition=self.use_resource.success_condition,
                failure_condition=self.use_resource.failure_condition,
                manifest=self.use_resource.get_manifest(self.template.command,
                                                        self.template.script))

        if self.success_hook is not None:
            assert isinstance(self.success_hook, HookStep)
            success_hook = deepcopy(self.success_hook)
            success_hook.expression = "%s.status == 'Succeeded'" % self.expr
            self.hooks["success"] = success_hook
        if self.running_hook is not None:
            assert isinstance(self.running_hook, HookStep)
            running_hook = deepcopy(self.running_hook)
            running_hook.expression = "%s.status == 'Running'" % self.expr
            self.hooks["running"] = running_hook
        if self.failure_hook is not None:
            assert isinstance(self.failure_hook, HookStep)
            failure_hook = deepcopy(self.failure_hook)
            failure_hook.expression = "%s.status == 'Failed'" % self.expr
            self.hooks["failure"] = failure_hook

    def convert_to_argo(self, context=None):
        logging.debug("handle step %s" % self.name)
        self.prepare_argo_arguments(context)
        if isinstance(self.when, ArgoVar):
            self.when = "{{=%s}}" % self.when.expr
        return V1alpha1WorkflowStep(
            name=self.name, template=self.template.name,
            arguments=V1alpha1Arguments(
                parameters=self.argo_parameters,
                artifacts=self.argo_artifacts
            ), when=self.when, with_param=self.with_param,
            with_sequence=None if self.with_sequence is None else
            self.with_sequence.convert_to_argo(),
            continue_on=V1alpha1ContinueOn(failed=self.continue_on_failed,
                                           error=self.continue_on_error),
            hooks={
                name: hook.convert_to_argo(context)
                for name, hook in self.hooks.items()
            },
        )

    def convert_to_graph(self):
        if isinstance(self._with_param, ArgoVar):
            self._with_param = "{{=%s}}" % self._with_param.expr
        if isinstance(self.when, ArgoVar):
            self.when = "{{=%s}}" % self.when.expr

        parameters = {
            k: v["value"] for k, v in
            self.inputs.parameters.convert_to_graph().items()
            if not k.startswith("dflow_") and "value" in v
        }
        artifacts = {
            k: v["source"] for k, v in
            self.inputs.artifacts.convert_to_graph().items()
            if not k.startswith("dflow_") and v["source"] is not None
        }
        return {
            "name": self.name,
            "template": self.template.name,
            "with_param": self._with_param,
            "with_sequence": self._with_sequence.to_dict() if isinstance(
                self._with_sequence, ArgoSequence) else self._with_sequence,
            "slices": self._slices,
            "parameters": parameters,
            "artifacts": artifacts,
            "continue_on_failed": self.continue_on_failed,
            "continue_on_error": self.continue_on_error,
            "continue_on_num_success": self.continue_on_num_success,
            "continue_on_success_ratio": self.continue_on_success_ratio,
            "when": self.when,
            "key": self.key,
            "executor": self.executor,
            "use_resource": self.use_resource,
            "util_image": self.util_image,
            "util_image_pull_policy": self.util_image_pull_policy,
            "util_command": self.util_command,
        }

    @classmethod
    def from_graph(cls, graph, templates):
        template = templates[graph["template"]]
        graph["template"] = template
        for k in template.inputs.artifacts:
            if not k.startswith("dflow_") and k not in graph["artifacts"]:
                graph["artifacts"] = graph.get("artifacts", {})
                graph["artifacts"][k] = None
        if isinstance(graph.get("with_sequence"), dict):
            graph["with_sequence"] = ArgoSequence.from_dict(
                graph["with_sequence"])
        return cls(**graph)

    def run(self, scope, context=None, order=None):
        self.phase = "Pending"
        self.render_by_executor(context)

        if self.when is not None:
            if isinstance(self.when, (InputParameter, OutputParameter)):
                value = get_var(self.when, scope).value
            elif isinstance(self.when, ArgoVar):
                value = expression(self.when.expr).eval(scope)
            elif isinstance(self.when, str):
                value = eval_expr(render_expr(self.when, scope))
            if not value:
                self.phase = "Skipped"
                return

        for name, par in list(self.inputs.parameters.items()):
            if par.save_as_artifact:
                if hasattr(par, "value"):
                    path = os.path.abspath(
                        os.path.join("..", config["debug_artifact_dir"],
                                     "upload/%s/%s" % (uuid.uuid4(), name)))
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as f:
                        f.write(jsonpickle.dumps(par.value))
                    self.inputs.artifacts["dflow_bigpar_" + name] = \
                        InputArtifact(path=par.path, source=S3Artifact(path))
                elif par.source is not None:
                    self.inputs.artifacts["dflow_bigpar_" + name] = \
                        InputArtifact(path=par.path,
                                      source=get_var(par.source, scope))
                if "dflow_bigpar_" + name not in \
                        self.template.inputs.artifacts:
                    self.template.inputs.artifacts["dflow_bigpar_" + name] = \
                        InputArtifact(path=par.path)
                if name in self.template.inputs.parameters:
                    del self.template.inputs.parameters[name]
                del self.inputs.parameters[name]

        for name, par in list(self.outputs.parameters.items()):
            if par.save_as_artifact:
                if name in self.template.outputs.parameters:
                    par = self.template.outputs.parameters[name]
                    kwargs = {
                        "global_name": "dflow_bigpar_" + par.global_name
                        if par.global_name is not None else None
                    }
                    if par.value_from_path is not None:
                        art = OutputArtifact(
                            path=par.value_from_path, **kwargs)
                    elif par.value_from_parameter is not None:
                        art = OutputArtifact(
                            _from=str(par.value_from_parameter), **kwargs)
                    elif par.value_from_expression is not None:
                        art = OutputArtifact(from_expression=str(
                            par.value_from_expression), **kwargs)
                    self.template.outputs.artifacts[
                        "dflow_bigpar_" + name] = art
                    if not par.save_both:
                        del self.template.outputs.parameters[name]
                self.outputs.artifacts["dflow_bigpar_" + name] = deepcopy(
                    self.template.outputs.artifacts["dflow_bigpar_" + name])
                if not par.save_both:
                    del self.outputs.parameters[name]

        # source input parameters
        parameters = InputParameters({k: copy(v) for k, v in
                                      self.inputs.parameters.items()})
        for k, v in self.template.outputs.parameters.items():
            if hasattr(v, "value"):
                self.outputs.parameters[k].value = v.value
        for name, par in parameters.items():
            value = par.value

            def handle_expr(val, scope):
                if isinstance(val, dict):
                    for k, v in val.items():
                        if isinstance(v, ArgoVar):
                            val[k] = expression(v.expr).eval(scope)
                        else:
                            handle_expr(v, scope)
                elif isinstance(val, list):
                    for i, v in enumerate(val):
                        if isinstance(v, ArgoVar):
                            val[i] = expression(v.expr).eval(scope)
                        else:
                            handle_expr(v, scope)
                elif hasattr(val, "__dict__"):
                    for k, v in val.__dict__.items():
                        if isinstance(v, ArgoVar):
                            val.__dict__[k] = expression(v.expr).eval(scope)
                        else:
                            handle_expr(v, scope)

            if isinstance(value, (InputParameter, OutputParameter)):
                par.value = get_var(value, scope).value
            elif isinstance(value, ArgoVar):
                par.value = expression(value.expr).eval(scope)
            elif isinstance(value, str):
                par.value = render_expr(value, scope)
            else:
                try:
                    handle_expr(par.value, scope)
                except Exception as e:
                    logging.warning("Failed to handle expressions in parameter"
                                    " value: %s" % e)

        # source input artifacts
        for name, art in self.template.inputs.artifacts.items():
            if name not in self.inputs.artifacts and art.source is not None:
                self.inputs.artifacts[name] = deepcopy(art)
        for name, art in self.inputs.artifacts.items():
            if isinstance(art.source, (InputArtifact, OutputArtifact)):
                art.source = get_var(art.source, scope)

        if self.with_param is not None or self.with_sequence is not None:
            if isinstance(self.with_param, (InputParameter,
                                            OutputParameter)):
                item_list = self.with_param.value
            elif isinstance(self.with_param, ArgoVar):
                item_list = expression(self.with_param.expr).eval(scope)
                if isinstance(item_list, str):
                    item_list = eval(item_list)
            elif isinstance(self.with_param, str):
                self.with_param = render_expr(self.with_param, scope)
                item_list = eval(self.with_param)
            elif hasattr(self.with_param, "__iter__"):
                item_list = list(self.with_param)
            elif self.with_sequence is not None:
                start = 0
                if self.with_sequence.start is not None:
                    start = self.with_sequence.start
                    if isinstance(start, (InputParameter, OutputParameter)):
                        start = start.value
                    elif isinstance(start, ArgoVar):
                        start = int(expression(start.expr).eval(scope))
                if self.with_sequence.count is not None:
                    count = self.with_sequence.count
                    if isinstance(count, (InputParameter, OutputParameter)):
                        count = count.value
                    elif isinstance(count, ArgoVar):
                        count = int(expression(count.expr).eval(scope))
                    sequence = list(range(start, start + count))
                if self.with_sequence.end is not None:
                    end = self.with_sequence.end
                    if isinstance(end, (InputParameter, OutputParameter)):
                        end = end.value
                    elif isinstance(end, ArgoVar):
                        end = int(expression(end.expr).eval(scope))
                    if end >= start:
                        sequence = list(range(start, end + 1))
                    else:
                        sequence = list(range(start, end - 1, -1))
                if self.with_sequence.format is not None:
                    item_list = [self.with_sequence.format % i
                                 for i in sequence]
                else:
                    item_list = sequence
            else:
                raise RuntimeError("Not supported")

            # avoid exponentially increase of memory
            self.parallel_steps = [deepcopy(self) for _ in item_list]
            assert isinstance(item_list, list)
            import concurrent.futures
            cwd = os.getcwd()
            max_workers = config["debug_pool_workers"]
            if max_workers == -1:
                max_workers = len(item_list)
            if max_workers is None:
                max_workers = os.cpu_count() or 1
            max_workers = min(max_workers, len(item_list)) or 1
            with ProcessPoolExecutor(max_workers) as pool:
                futures = []
                scope_copy = deepcopy(scope)
                for i, item in enumerate(item_list):
                    ps = self.parallel_steps[i]
                    ps.phase = "Pending"
                    try:
                        future = pool.submit(
                            ps.exec_with_config, scope_copy, parameters, item,
                            config, s3_config, cwd, context,
                            "%s-%s" % (order, i))
                    except concurrent.futures.process.BrokenProcessPool as e:
                        # retrieve exception of subprocess before exit
                        for future in concurrent.futures.as_completed(futures):
                            future.result()
                        raise e
                    futures.append(future)
                    if config["debug_batch_size"] and i != len(item_list) - 1 \
                            and (i+1) % config["debug_batch_size"] == 0:
                        logging.info("Wait %s seconds before submitting next "
                                     "batch" % config["debug_batch_interval"])
                        time.sleep(config["debug_batch_interval"])

                failed = []
                for future in concurrent.futures.as_completed(futures):
                    j = futures.index(future)
                    try:
                        phase, pars, arts = future.result()
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        self.parallel_steps[j].phase = "Failed"
                        if not self.continue_on_failed:
                            self.phase = "Failed"
                            if config["debug_failfast"]:
                                raise RuntimeError("Step %s failed" %
                                                   self.parallel_steps[j])
                            else:
                                failed.append(self.parallel_steps[j])
                    else:
                        for name, value in pars.items():
                            self.parallel_steps[j].outputs.parameters[
                                name].value = value
                        for name, path in arts.items():
                            self.parallel_steps[j].outputs.artifacts[
                                name].local_path = path
                        logging.info("Outputs of %s collected" %
                                     self.parallel_steps[j])
                if len(failed) > 0:
                    raise RuntimeError("Step %s failed" % failed)

            for name, par in self.outputs.parameters.items():
                par.value = []
                for ps in self.parallel_steps:
                    if hasattr(ps.outputs.parameters[name], "value"):
                        value = ps.outputs.parameters[name].value
                        if isinstance(value, str):
                            par.value.append(value)
                        else:
                            par.value.append(jsonpickle.dumps(value))
            for name, art in self.outputs.artifacts.items():
                for save in self.template.outputs.artifacts[name].save:
                    if isinstance(save, S3Artifact):
                        key = render_script(save.key, parameters,
                                            scope.workflow_id)
                        art.local_path = os.path.abspath(os.path.join(
                            "..", config["debug_artifact_dir"], key))
            self.phase = "Succeeded"
        else:
            try:
                self.exec(scope, parameters, None, context, order)
            except Exception:
                self.phase = "Failed"
                if not self.continue_on_failed:
                    raise RuntimeError("Step %s failed" % self)

    def run_with_config(self, scope, context, conf, s3_conf, cwd, order):
        logging.info("Step %s starts in process %s" % (self.name, os.getpid()))
        config.update(conf)
        s3_config.update(s3_conf)
        os.chdir(cwd)
        self.run(scope, context, order)
        logging.info("Step %s finishes in process %s" % (
            self.name, os.getpid()))
        pars = {name: par.value for name, par in
                self.outputs.parameters.items() if hasattr(par, "value")}
        arts = {name: art.local_path for name, art in
                self.outputs.artifacts.items() if hasattr(art, "local_path")}
        return self.phase, pars, arts

    def record_input_parameters(self, stepdir, parameters):
        os.makedirs(os.path.join(stepdir, "inputs/parameters"), exist_ok=True)
        for name, par in parameters.items():
            par_path = os.path.join(stepdir, "inputs/parameters/%s" % name)
            with open(par_path, "w") as f:
                f.write(par.value if isinstance(par.value, str)
                        else jsonpickle.dumps(par.value))
            if par.type is not None:
                os.makedirs(os.path.join(
                    stepdir, "inputs/parameters/.dflow"), exist_ok=True)
                with open(os.path.join(
                        stepdir, "inputs/parameters/.dflow/%s" % name),
                        "w") as f:
                    f.write(jsonpickle.dumps({"type": type_to_str(par.type)}))

    def record_input_artifacts(self, stepdir, artifacts, item, scope,
                               ignore_nonexist=False):
        os.makedirs(os.path.join(stepdir, "inputs/artifacts"), exist_ok=True)
        for name, art in artifacts.items():
            art_path = os.path.join(stepdir, "inputs/artifacts/%s" % name)
            if isinstance(art.source, str) and art.source.startswith("{{"):
                if "/" in art.source:
                    i = art.source.find("}}")
                    art.sp = art.source[i+3:]
                    art.source = art.source[:i+2]
                if art.source.startswith("{{workflow.outputs.artifacts."):
                    art.source = LocalArtifact("%s/../outputs/artifacts/%s" % (
                        stepdir, art.source[29:-2]))
                else:
                    art.source = get_var(art.source, scope)
            if isinstance(art.source, S3Artifact) and art.source.local_path \
                    is None:
                path = os.path.abspath(os.path.join(
                    stepdir, "..", config["debug_artifact_dir"],
                    art.source.key[:-4] if art.source.key.endswith(".tgz")
                    else art.source.key))
                download_with_lock(
                    lambda: download_artifact_debug(
                        artifact=art.source, path=os.path.dirname(path)), path)
                assert os.path.exists(path), "S3 key of the input art"\
                    "ifact %s: %s does not exist" % (name, art.source.key)
                art.source.local_path = path
            elif isinstance(art.source, HTTPArtifact) and not hasattr(
                    art.source, "local_path"):
                path = os.path.abspath(os.path.join(
                    stepdir, "..", config["debug_artifact_dir"],
                    art.source.url.split("?")[0]))
                if path.endswith(".tgz"):
                    download_with_lock(
                        lambda: untar(art.source.download(
                            path=os.path.dirname(path))), path[:-4])
                    path = path[:-4]
                else:
                    download_with_lock(
                        lambda: art.source.download(
                            path=os.path.dirname(path)), path)
                art.source.local_path = path
            if isinstance(
                art.source, (InputArtifact, OutputArtifact, LocalArtifact,
                             S3Artifact, HTTPArtifact)):
                sub_path = None
                if getattr(art.source, "_sub_path", None) is not None:
                    sub_path = art.source._sub_path
                if art.sp is not None:
                    if sub_path is None:
                        sub_path = art.sp
                    else:
                        sub_path += "/%s" % art.sp
                if sub_path is not None:
                    if item is not None:
                        sub_path = render_item(sub_path, item)
                    force_link(os.path.join(art.source.local_path, sub_path),
                               art_path)
                elif art.optional and not hasattr(art.source, 'local_path'):
                    continue
                else:
                    if config["dereference_symlink"]:
                        force_link(os.path.realpath(art.source.local_path),
                                   art_path)
                    else:
                        force_link(art.source.local_path, art_path)
            elif isinstance(art.source, str):
                with open(art_path, "w") as f:
                    f.write(art.source)
            elif art.source is None and art.optional:
                continue
            elif not ignore_nonexist:
                raise RuntimeError("Not supported: ", art.source)

    def record_output_parameters(self, stepdir, parameters):
        os.makedirs(os.path.join(stepdir, "outputs/parameters"), exist_ok=True)
        for name, par in parameters.items():
            par_path = os.path.join(stepdir,
                                    "outputs/parameters/%s" % name)
            if isinstance(par.value, str):
                value = par.value
            else:
                value = jsonpickle.dumps(par.value)
            with open(par_path, "w") as f:
                f.write(value)
            if par.type is not None or par.global_name is not None:
                metadata = {}
                if par.type is not None:
                    metadata["type"] = type_to_str(par.type)
                if par.global_name is not None:
                    metadata["globalName"] = par.global_name
                os.makedirs(os.path.join(
                    stepdir, "outputs/parameters/.dflow"), exist_ok=True)
                with open(os.path.join(
                        stepdir, "outputs/parameters/.dflow/%s" % name),
                        "w") as f:
                    f.write(jsonpickle.dumps(metadata))
            if par.global_name is not None:
                os.makedirs(os.path.join(stepdir, "../outputs/parameters"),
                            exist_ok=True)
                global_par_path = os.path.join(
                    stepdir, "../outputs/parameters/%s" % par.global_name)
                if os.path.exists(global_par_path):
                    os.remove(global_par_path)
                os.symlink(par_path, global_par_path)

    def record_output_artifacts(self, stepdir, artifacts):
        os.makedirs(os.path.join(stepdir, "outputs/artifacts"), exist_ok=True)
        for name, art in artifacts.items():
            if art.optional and not hasattr(art, "local_path"):
                continue
            art_path = os.path.join(stepdir, "outputs/artifacts/%s" % name)
            force_link(art.local_path, art_path)
            if art.global_name is not None:
                metadata = {"globalName": art.global_name}
                os.makedirs(os.path.join(
                    stepdir, "outputs/artifacts/.dflow"), exist_ok=True)
                with open(os.path.join(
                        stepdir, "outputs/artifacts/.dflow/%s" % name),
                        "w") as f:
                    f.write(jsonpickle.dumps(metadata))
                os.makedirs(os.path.join(stepdir, "../outputs/artifacts"),
                            exist_ok=True)
                global_art_path = os.path.join(
                    stepdir, "../outputs/artifacts/%s" % art.global_name)
                while True:
                    try:
                        os.symlink(art_path, global_art_path)
                        break
                    except FileExistsError:
                        # for race condition of removing symlink
                        try:
                            os.remove(global_art_path)
                        except FileNotFoundError:
                            pass

    def load_output_parameters(self, stepdir, parameters):
        for name, par in parameters.items():
            par_path = os.path.join(stepdir,
                                    "outputs/parameters/%s" % name)
            with open(par_path, "r") as f:
                if par.type is None or par.type == str:
                    par.value = f.read()
                else:
                    par.value = jsonpickle.loads(f.read())

    def load_output_artifacts(self, stepdir, artifacts):
        for name, art in artifacts.items():
            art_path = os.path.join(stepdir,
                                    "outputs/artifacts/%s" % name)
            art.local_path = art_path

    def exec(self, scope, parameters, item=None, context=None, order=None):
        # render item
        if item is not None:
            for par in parameters.values():
                if isinstance(par.value, str):
                    par.value = render_item(par.value, item)
            for art in self.inputs.artifacts.values():
                if isinstance(art.source, S3Artifact):
                    art.source.key = render_item(art.source.key, item)
                elif isinstance(art.source, HTTPArtifact):
                    art.source.url = render_item(art.source.url, item)

        from .dag import DAG
        from .steps import Steps
        if isinstance(self.template, (DAG, Steps)):
            self.exec_steps(scope, parameters, item, context, order)
        else:
            self.exec_pod(scope, parameters, item, order)

    def add_children(self, scope, step_id, order):
        if scope.stepdir is not None:
            children_file = os.path.join(scope.stepdir, "children")
            from filelock import FileLock
            with FileLock(children_file + ".lock"):
                if os.path.isfile(children_file):
                    with open(children_file, "r") as f:
                        children = json.load(f)
                else:
                    children = {}
                if order not in children:
                    children[order] = step_id
                    with open(children_file, "w") as f:
                        json.dump(children, f)

    def get_children(self, scope, order):
        if scope.stepdir is not None:
            if os.path.isfile(os.path.join(scope.stepdir, "children")):
                with open(os.path.join(scope.stepdir, "children"), "r") as f:
                    children = json.load(f)
                    return children.get(order)
        return None

    def exec_steps(self, scope, parameters, item=None, context=None,
                   order=None):
        if hasattr(self.template, "orig_template"):
            steps = deepcopy(self.template.orig_template)
            steps.orig_template = self.template.orig_template
        else:
            steps = deepcopy(self.template)
            steps.orig_template = self.template

        # override default inputs with arguments
        for name, par in parameters.items():
            steps.inputs.parameters[name].value = par.value

        if "dflow_key" in steps.inputs.parameters and \
                steps.inputs.parameters["dflow_key"].value:
            step_id = steps.inputs.parameters["dflow_key"].value
        else:
            step_id = self.get_children(scope, order)
            if step_id is None:
                while True:
                    step_id = "%s-%s-%s" % (scope.workflow_id, self.name,
                                            randstr())
                    stepdir = os.path.abspath(step_id)
                    if not os.path.exists(stepdir):
                        break

        stepdir = os.path.abspath(step_id)
        if os.path.exists(stepdir):
            with open(os.path.join(stepdir, "phase"), "r") as f:
                self.phase = f.read()
            if self.phase == "Succeeded":
                logging.warning("step (key: %s) skipped" % step_id)
                self.load_output_parameters(stepdir, self.outputs.parameters)
                self.load_output_artifacts(stepdir, self.outputs.artifacts)
                self.add_children(scope, step_id, order)
                return
            logging.warning("step (key: %s) restarting" % step_id)
        else:
            os.makedirs(stepdir)

        self.add_children(scope, step_id, order)
        if self.phase == "Pending":
            from .dag import DAG
            from .steps import Steps
            with open(os.path.join(stepdir, "type"), "w") as f:
                if isinstance(self.template, Steps):
                    f.write("Steps")
                elif isinstance(self.template, DAG):
                    f.write("DAG")
            with open(os.path.join(stepdir, "phase"), "w") as f:
                f.write("Pending")
            with open(os.path.join(stepdir, "name"), "w") as f:
                f.write(self.name)
            self.record_input_parameters(stepdir, steps.inputs.parameters)
            self.record_input_artifacts(stepdir, self.inputs.artifacts,
                                        item, scope, True)

        for name, art in self.inputs.artifacts.items():
            art_path = os.path.join(stepdir, "inputs/artifacts/%s" % name)
            if os.path.exists(art_path):
                steps.inputs.artifacts[name].local_path = art_path

        self.phase = "Running"
        with open(os.path.join(stepdir, "phase"), "w") as f:
            f.write("Running")
        try:
            steps.run(scope.workflow_id, context, stepdir)
        except Exception:
            self.phase = "Failed"
            with open(os.path.join(stepdir, "phase"), "w") as f:
                f.write("Failed")
            raise RuntimeError("Step %s failed" % self)

        for name, par in self.outputs.parameters.items():
            par1 = self.template.outputs.parameters[name]
            if par1.value_from_parameter is not None:
                try:
                    par.value = get_var(par1.value_from_parameter, steps).value
                except Exception as e:
                    if hasattr(par1, "default"):
                        par.value = par1.default
                    else:
                        raise e
            elif par1.value_from_expression is not None:
                if isinstance(par1.value_from_expression, ArgoVar):
                    par1.value_from_expression = expression(
                        par1.value_from_expression.expr)
                elif isinstance(par1.value_from_expression, str):
                    par1.value_from_expression = expression(
                        par1.value_from_expression)
                par.value = par1.value_from_expression.eval(steps)

        for name, art in self.outputs.artifacts.items():
            art1 = self.template.outputs.artifacts[name]
            if art1._from is not None:
                if isinstance(art1._from, str) and art1._from.startswith(
                        "{{workflow.outputs.artifacts."):
                    art.local_path = "%s/../outputs/artifacts/%s" % (
                        stepdir, art1._from[29:-2])
                else:
                    art.local_path = get_var(art1._from, steps).local_path
            elif art1.from_expression is not None:
                if isinstance(art1.from_expression, ArgoVar):
                    art1.from_expression = expression(
                        art1.from_expression.expr)
                elif isinstance(art1.from_expression, str):
                    art1.from_expression = expression(art1.from_expression)
                art.local_path = art1.from_expression.eval(steps)

        self.record_output_parameters(stepdir, self.outputs.parameters)
        self.record_output_artifacts(stepdir, self.outputs.artifacts)
        self.phase = "Succeeded"
        with open(os.path.join(stepdir, "phase"), "w") as f:
            f.write("Succeeded")

    def exec_pod(self, scope, parameters, item=None, order=None):
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
        cwd = os.getcwd()
        if "dflow_key" in parameters:
            step_id = parameters["dflow_key"].value
        else:
            step_id = self.get_children(scope, order)
            if step_id is None:
                while True:
                    step_id = "%s-%s-%s" % (scope.workflow_id, self.name,
                                            randstr())
                    stepdir = os.path.abspath(step_id)
                    if not os.path.exists(stepdir):
                        break

        stepdir = os.path.abspath(step_id)
        if os.path.exists(stepdir):
            with open(os.path.join(stepdir, "phase"), "r") as f:
                self.phase = f.read()
            if self.phase == "Succeeded":
                logging.warning("step (key: %s) skipped" % step_id)
                self.load_output_parameters(stepdir, self.outputs.parameters)
                self.load_output_artifacts(stepdir, self.outputs.artifacts)
                self.add_children(scope, step_id, order)
                os.chdir(cwd)
                return
            logging.warning("step (key: %s) restarting" % step_id)
        else:
            os.makedirs(stepdir)

        self.add_children(scope, step_id, order)
        self.stepdir = stepdir
        if self.phase == "Pending":
            with open(os.path.join(stepdir, "type"), "w") as f:
                f.write("Pod")
            with open(os.path.join(stepdir, "phase"), "w") as f:
                f.write("Pending")
            with open(os.path.join(stepdir, "name"), "w") as f:
                f.write(self.name)

        workdir = os.path.join(stepdir, "workdir")
        os.makedirs(workdir, exist_ok=True)
        os.chdir(workdir)

        if self.phase == "Pending":
            self.record_input_parameters(stepdir, parameters)

            self.record_input_artifacts(stepdir, self.inputs.artifacts, item,
                                        scope)

            # prepare inputs artifacts
            for name, art in self.inputs.artifacts.items():
                art_path = os.path.join(stepdir, "inputs/artifacts/%s" % name)
                path = self.template.inputs.artifacts[name].path
                path = "%s/%s" % (workdir, path)
                path = render_script(path, parameters,
                                     scope.workflow_id, step_id)
                os.makedirs(os.path.dirname(
                    os.path.abspath(path)), exist_ok=True)
                backup(path)
                if isinstance(
                        art.source,
                        InputArtifact) and art.source is None and art.optional:
                    pass
                elif config["debug_copy_method"] == "symlink":
                    os.symlink(art_path, path)
                elif config["debug_copy_method"] == "link":
                    try:
                        copy_file(art_path, path)
                    except FileNotFoundError:
                        pass
                elif config["debug_copy_method"] == "copy":
                    try:
                        copy_file(art_path, path, func=shutil.copy2)
                    except FileNotFoundError:
                        pass
                else:
                    raise ValueError("Unsupported copy method for debug mode.")

        # set default output parameters
        for name, par in self.outputs.parameters.items():
            if hasattr(par, "default"):
                par.value = par.default

        script_path = os.path.join(stepdir, "script")
        if self.phase == "Pending":
            # render variables in the script
            script = self.template.script
            if not self.template.script_rendered:
                if hasattr(self.template, "tmp_root"):
                    # do not modify self.template
                    template = deepcopy(self.template)
                    template.tmp_root = "%s%s" % (workdir, template.tmp_root)
                    template.render_script()
                    script = template.script
                else:
                    script = script.replace("/tmp", "%s/tmp" % workdir)
            os.makedirs("%s/tmp" % workdir, exist_ok=True)
            script = render_script(script, parameters, scope.workflow_id,
                                   step_id)
            with open(script_path, "w") as f:
                f.write(script)

        self.phase = "Running"
        with open(os.path.join(stepdir, "phase"), "w") as f:
            f.write("Running")
        import subprocess
        args = self.template.command + [script_path]
        with subprocess.Popen(
            args=args,
            env={**os.environ,
                 **self.template.envs} if self.template.envs else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as p:
            with open("%s/pid" % stepdir, "w") as f:
                f.write(str(p.pid))
            with open("%s/log.txt" % stepdir, "w") as f:
                line = p.stdout.readline().decode(
                    sys.stdout.encoding or "utf-8")
                while line:
                    sys.stdout.write(line)
                    f.write(line)
                    line = p.stdout.readline().decode(
                        sys.stdout.encoding or "utf-8")
            p.wait()
            ret_code = p.poll()
        if ret_code != 0:
            with open(os.path.join(stepdir, "phase"), "w") as f:
                f.write("Failed")
            raise RuntimeError("Run %s failed" % args)

        # generate output parameters
        for name, par in self.outputs.parameters.items():
            path = par.value_from_path
            if path is not None:
                path = "%s/%s" % (workdir, path)
                with open(path, "r") as f:
                    if par.type is None or par.type == str:
                        par.value = f.read()
                    else:
                        par.value = jsonpickle.loads(f.read())
            elif hasattr(par, "value"):
                if isinstance(par.value, str):
                    par.value = render_script(
                        par.value, parameters, scope.workflow_id,
                        step_id)
        self.record_output_parameters(stepdir, self.outputs.parameters)

        # save artifacts
        for name, art in self.outputs.artifacts.items():
            path = art.path
            path = "%s/%s" % (workdir, path)
            art.local_path = path
            for save in self.template.outputs.artifacts[name].save:
                if isinstance(save, S3Artifact):
                    key = render_script(save.key, parameters,
                                        scope.workflow_id, step_id)
                    save_path = os.path.join(
                        cwd, "..", config["debug_artifact_dir"], key)

                    def try_link(src, dst):
                        if os.path.islink(dst) or os.path.isfile(dst):
                            try:
                                os.remove(dst)
                            except Exception:
                                pass
                        try:
                            if config["debug_save_copy_method"] == "symlink":
                                os.symlink(src, dst)
                            elif config["debug_save_copy_method"] == "link":
                                os.link(src, dst)
                            elif config["debug_save_copy_method"] == "copy":
                                shutil.copy2(src, dst)
                        except Exception:
                            pass
                    if os.path.isfile(path):
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        try_link(path, save_path)
                    else:
                        os.makedirs(save_path, exist_ok=True)
                        merge_dir(path, save_path, try_link)
                    art.local_path = save_path
        self.record_output_artifacts(stepdir, self.outputs.artifacts)

        os.chdir(cwd)
        self.phase = "Succeeded"
        with open(os.path.join(stepdir, "phase"), "w") as f:
            f.write("Succeeded")

    def exec_with_config(self, scope, parameters, item, conf, s3_conf, cwd,
                         context=None, order=None):
        logging.info("Step %s with item %s starts in process %s" % (
            self.name, item, os.getpid()))
        config.update(conf)
        s3_config.update(s3_conf)
        os.chdir(cwd)
        self.exec(scope, parameters, item, context, order)
        logging.info("Step %s with item %s finishes in process %s" % (
            self.name, item, os.getpid()))
        pars = {name: par.value for name, par in
                self.outputs.parameters.items() if hasattr(par, "value")}
        arts = {name: art.local_path for name, art in
                self.outputs.artifacts.items() if hasattr(art, "local_path")}
        return self.phase, pars, arts


class HookStep(Step):
    def __init__(
        self,
        template: OPTemplate,
        expression: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(name=randstr(), template=template, **kwargs)
        self.expression = expression

    def convert_to_argo(self, context=None):
        self.prepare_argo_arguments(context)
        return V1alpha1LifecycleHook(
            arguments=V1alpha1Arguments(
                parameters=self.argo_parameters,
                artifacts=self.argo_artifacts
            ),
            expression=self.expression,
            template=self.template.name,
        )


def render_item(expr, item):
    i = expr.find("{{")
    while i >= 0:
        j = expr.find("}}", i+2)
        var = expr[i+2:j]
        fields = var.split(".")
        if expr[i:i+3] == "{{=":
            value = eval(expr[i+3:j], {"item": item})
            expr = expr[:i] + value.strip() + expr[j+2:]
        elif fields[0] == "item":
            value = item
            for key in fields[1:]:
                value = value[key]
            value = value if isinstance(value, str) else \
                jsonpickle.dumps(value)
            expr = expr[:i] + value.strip() + expr[j+2:]
        i = expr.find("{{", i+1)
    return expr


def render_expr(expr, scope):
    # render variables
    i = expr.find("{{")
    while i >= 0:
        j = expr.find("}}", i+2)
        if expr[i:i+3] == "{{=":
            value = expression(expr[i+3:j]).eval(scope)
            value = value if isinstance(value, str) else \
                jsonpickle.dumps(value)
            expr = expr[:i] + value.strip() + expr[j+2:]
        else:
            var = get_var(expr[i:j+2], scope)
            if var:
                value = var.value
                value = value if isinstance(value, str) else \
                    jsonpickle.dumps(value)
                expr = expr[:i] + value.strip() + expr[j+2:]
        i = expr.find("{{", i+1)
    return expr


def get_var(expr, scope):
    sub_path = getattr(expr, "_sub_path", None)
    expr = str(expr)
    if expr[:2] == "{{" and expr[-2:] == "}}":
        expr = expr[2:-2]
    fields = expr.split(".")
    if fields[:2] == ["inputs", "parameters"]:
        name = fields[2]
        return scope.inputs.parameters[name]
    elif fields[:2] == ["inputs", "artifacts"]:
        name = fields[2]
        if sub_path is None:
            return scope.inputs.artifacts[name]
        else:
            return scope.inputs.artifacts[name].sub_path(sub_path)
    elif fields[0] in ["steps", "tasks"] and \
            fields[2:4] == ["outputs", "parameters"]:
        step_name = fields[1]
        name = fields[4]
        for step in scope:
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
        for step in scope:
            if isinstance(step, list):
                for ps in step:
                    if ps.name == step_name:
                        if sub_path is None:
                            return ps.outputs.artifacts[name]
                        else:
                            return ps.outputs.artifacts[name].sub_path(
                                sub_path)
            elif step.name == step_name:
                if sub_path is None:
                    return step.outputs.artifacts[name]
                else:
                    return step.outputs.artifacts[name].sub_path(sub_path)
        raise RuntimeError("Parse failed: %s" % expr)
    elif fields[0] == "item":
        return None  # ignore
    elif fields == ["workflow", "name"]:
        return InputParameter(value=scope.workflow_id)
    elif fields[:3] == ["workflow", "outputs", "artifacts"]:
        return LocalArtifact("%s/../outputs/artifacts/%s" % (
            scope.stepdir, fields[3]))
    else:
        raise RuntimeError("Not supported: %s" % expr)


def eval_expr(expr):
    if expr == "true":
        return True
    elif expr == "false":
        return False
    expr_list = expr.split()
    assert (len(expr_list) == 3), "Expression (%s) not supported" % expr
    operator = expr_list[1]
    if operator == "==":
        return expr_list[0] == expr_list[2]
    elif operator == "!=":
        return expr_list[0] != expr_list[2]
    expr_right = float(expr_list[2])
    expr_left = float(expr_list[0])
    if operator == "<=":
        return expr_left <= expr_right
    elif operator == "<":
        return expr_left < expr_right
    elif operator == ">=":
        return expr_left >= expr_right
    elif operator == ">":
        return expr_left > expr_right
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
        if var[:1] == "=":
            var = var[1:]
        fields = var.split(".")
        if fields[0] == "inputs" and fields[1] == "parameters":
            par = fields[2]
            if par in parameters:
                value = parameters[par].value
                script = script[:i] + (value if isinstance(value, str) else
                                       jsonpickle.dumps(value)) + script[j+2:]
        else:
            raise RuntimeError("Not supported: %s" % var)
        i = script.find("{{", i+1)
    return script


def backup(path):
    cnt = 0
    bk = path
    while os.path.exists(bk) or os.path.islink(bk):
        cnt += 1
        bk = path + ".bk%s" % cnt
    if bk != path:
        shutil.move(path, bk)


def expression(expr):
    return Expression(replace_argo_func(expr))


def replace_argo_func(expr):
    i = expr.find("toJson(map(sprig.untilStep(0, ")
    j = expr.find(", 1), { {'order': #")
    k = expr.find("} }))")
    if i != -1 and j != -1 and k != -1:
        v = expr[j+19:k].replace(
            "jsonpath(", "(lambda x: eval(x) if isinstance(x, str) else x)("
        ).replace(", '$')[#]", ")[i]")
        expr = "str([{'order': i" + v + "} for i in range(" + expr[i+30:j] \
            + ")])"
    expr = expr.replace("toJson", "str")
    expr = expr.replace("sprig.fromJson",
                        "(lambda x: eval(x) if isinstance(x, str) else x)")
    expr = expr.replace("sprig.untilStep",
                        "(lambda *x: list(range(*list(map(int, x)))))")
    expr = expr.replace("sprig.atoi", "int")
    expr = expr.replace(" ? ", " and ")
    expr = expr.replace(" : ", " or ")
    expr = expr.replace("asFloat", "float")
    expr = expr.replace("jsonpath",
                        "(lambda x, y: eval(x) if isinstance(x, str) else x)")
    expr = expr.replace("string", "str")
    expr = expr.replace("sprig.int", "int")
    return expr


def add_slices(templ: OPTemplate, slices: Slices, layer=0):
    slice_par = "dflow_slice" if layer == 0 else "dflow_slice_%s" % layer
    slice_par_1 = "dflow_slice_%s" % (layer + 1)
    templ.inputs.parameters[slice_par] = InputParameter(value="None")

    steps = []
    for s in templ:
        if isinstance(s, list):
            steps += s
        else:
            steps.append(s)

    for name in slices.input_parameter:
        for step in steps:
            for par in list(step.inputs.parameters.values()):
                # input parameter referring to sliced input parameter
                if getattr(par, "value", None) is templ.inputs.parameters[
                        name] or par.source is templ.inputs.parameters[name]:
                    templ.inputs.parameters["dflow_skip_slice_input"] = \
                        InputParameter(value=0)
                    if hasattr(step.template, "set_skip_slice_input"):
                        step.template.set_skip_slice_input()
                    else:
                        step.template.inputs.parameters[
                            "dflow_skip_slice_input"] = InputParameter(value=0)
                    step.template.inputs.parameters[slice_par_1] = \
                        InputParameter()
                    step.template.add_slices(Slices(
                        "{{inputs.parameters.%s}}" % slice_par_1,
                        input_parameter=[par.name],
                        sub_path=slices.sub_path,
                        pool_size=slices.pool_size), layer=layer+1)
                    step.inputs.parameters[slice_par_1] = InputParameter(
                        value="{{inputs.parameters.%s}}" % slice_par)
                    step.inputs.parameters["dflow_skip_slice_input"] = \
                        InputParameter(value="{{inputs.parameters."
                                       "dflow_skip_slice_input}}")

    for name in slices.input_artifact:
        if slices.sub_path:
            templ.inputs.parameters["dflow_%s_sub_path" % name] = \
                InputParameter()
        for step in steps:
            for art in list(step.inputs.artifacts.values()):
                # input artifact referring to sliced input artifact
                if name in templ.inputs.artifacts:
                    source_slice = art.source is templ.inputs.artifacts[
                        name] or getattr(art.source, "parent", None) is \
                        templ.inputs.artifacts[name]
                    art_name = art.name
                else:
                    source_slice = any([art.source is a or getattr(
                        art.source, "parent", None) is a for n, a in
                        templ.inputs.artifacts.items() if n.startswith(
                        "dflow_%s_" % name)])
                    art_name = art.name[6:art.name.rfind("_")]
                if source_slice:
                    templ.inputs.parameters["dflow_skip_slice_input"] = \
                        InputParameter(value=0)
                    if hasattr(step.template, "set_skip_slice_input"):
                        step.template.set_skip_slice_input()
                    else:
                        step.template.inputs.parameters[
                            "dflow_skip_slice_input"] = InputParameter(value=0)
                    step.template.inputs.parameters[slice_par_1] = \
                        InputParameter()
                    step.template.add_slices(Slices(
                        "{{inputs.parameters.%s}}" % slice_par_1,
                        input_artifact=[art_name],
                        sub_path=slices.sub_path,
                        pool_size=slices.pool_size), layer=layer+1)
                    step.inputs.parameters[slice_par_1] = InputParameter(
                        value="{{inputs.parameters.%s}}" % slice_par)
                    step.inputs.parameters["dflow_skip_slice_input"] = \
                        InputParameter(value="{{inputs.parameters."
                                       "dflow_skip_slice_input}}")
                    if slices.sub_path:
                        step.inputs.parameters[
                            "dflow_%s_sub_path" % art_name] = InputParameter(
                            value="{{inputs.parameters.dflow_%s_sub_path}}"
                            % name)

    def stack_output_parameter(par):
        if isinstance(par, OutputParameter):
            step = par.step
            if step.template is templ:
                templ.inputs.parameters["dflow_skip_slice_input"] = \
                    InputParameter(value=0)
                step.inputs.parameters["dflow_skip_slice_input"] = \
                    InputParameter(value=1)
                step.inputs.parameters[slice_par] = InputParameter(
                    value="{{inputs.parameters.%s}}" % slice_par)
                return
            step.template.inputs.parameters[slice_par_1] = InputParameter()
            step.template.add_slices(Slices(
                "{{inputs.parameters.%s}}" % slice_par_1,
                output_parameter=[par.name],
                sub_path=slices.sub_path,
                pool_size=slices.pool_size), layer=layer+1)
            step.inputs.parameters[slice_par_1] = InputParameter(
                value="{{inputs.parameters.%s}}" % slice_par)

    for name in slices.output_parameter:
        # sliced output parameter from
        if templ.outputs.parameters[name].value_from_parameter is not None:
            stack_output_parameter(
                templ.outputs.parameters[name].value_from_parameter)
        elif templ.outputs.parameters[name].value_from_expression is not None:
            stack_output_parameter(
                templ.outputs.parameters[name].value_from_expression._then)
            stack_output_parameter(
                templ.outputs.parameters[name].value_from_expression._else)

    def stack_output_artifact(art):
        if isinstance(art, OutputArtifact):
            step = art.step
            if step.template is templ:
                templ.inputs.parameters["dflow_skip_slice_input"] = \
                    InputParameter(value=0)
                step.inputs.parameters["dflow_skip_slice_input"] = \
                    InputParameter(value=1)
                step.inputs.parameters[slice_par] = InputParameter(
                    value="{{inputs.parameters.%s}}" % slice_par)
                return
            step.template.inputs.parameters[slice_par_1] = InputParameter()
            step.template.add_slices(Slices(
                "{{inputs.parameters.%s}}" % slice_par_1,
                output_artifact=[art.name],
                sub_path=slices.sub_path,
                pool_size=slices.pool_size, create_dir=slices.create_dir),
                layer=layer+1)
            step.inputs.parameters[slice_par_1] = InputParameter(
                value="{{inputs.parameters.%s}}" % slice_par)

    for name in slices.output_artifact:
        # sliced output artifact from
        if templ.outputs.artifacts[name]._from is not None:
            stack_output_artifact(templ.outputs.artifacts[name]._from)
        elif templ.outputs.artifacts[name].from_expression is not None:
            stack_output_artifact(
                templ.outputs.artifacts[name].from_expression._then)
            stack_output_artifact(
                templ.outputs.artifacts[name].from_expression._else)


def untar(tf_path):
    tf = tarfile.open(tf_path, "r:gz")
    path = tf_path[:-4]
    tf.extractall(path)
    tf.close()
    os.remove(tf_path)

    # if the tarball contains only one file or directory,
    # return its path
    ld = os.listdir(path)
    if len(ld) == 1:
        os.rename(os.path.join(path, ld[0]), path + ".tmp")
        os.rmdir(path)
        os.rename(path + ".tmp", path)
    return path


def download_artifact_debug(artifact, path):
    key = get_key(artifact)

    if key[-4:] == ".tgz":
        download_s3(key=key, path=path)
        return untar(os.path.join(path, os.path.basename(key)))
    else:
        download_s3(key=key, path=path, keep_dir=True)
        return os.path.join(path, os.path.basename(key))


def download_with_lock(download, path):
    from filelock import FileLock
    with FileLock(path + ".lock"):
        if os.path.exists(path):
            pass
        else:
            download()
