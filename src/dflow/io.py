import json
import tempfile
from collections import UserDict
from copy import copy, deepcopy
from typing import Any, Dict, List, Optional, Union

from .common import (CustomArtifact, HTTPArtifact, LocalArtifact, S3Artifact,
                     jsonpickle, param_errmsg, param_regex)
from .config import config
from .utils import randstr, s3_config, upload_s3

try:
    from argo.workflows.client import (V1alpha1ArchiveStrategy,
                                       V1alpha1HTTPArtifact, V1alpha1Inputs,
                                       V1alpha1Outputs, V1alpha1RawArtifact)

    from .client import V1alpha1Artifact, V1alpha1Parameter, V1alpha1ValueFrom
except Exception:
    pass

NotAllowedInputArtifactPath = ["/", "/tmp"]


def type_to_str(type):
    if hasattr(type, "__module__") and hasattr(type, "__name__"):
        if type.__module__ == "builtins":
            return type.__name__
        else:
            return "%s.%s" % (type.__module__, type.__name__)
    else:
        return str(type)


class ObjectDict(UserDict):
    def __getattr__(self, key):
        if key == "data":
            return super().__getattr__(key)
        return self.data[key]


def to_expr(var):
    if isinstance(var, ArgoVar):
        return var.expr
    return str(var)


class Expression:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return self.expr

    def eval(self, scope):
        from .dag import DAG
        from .steps import Steps
        inputs = ObjectDict()
        inputs["parameters"] = ObjectDict({
            k: v.value for k, v in scope.inputs.parameters.items()
        })
        steps = ObjectDict()
        if isinstance(scope, Steps):
            for step in sum([s if isinstance(s, list) else [s]
                             for s in scope], []):
                steps[step.name] = ObjectDict({"outputs": ObjectDict({
                    "parameters": ObjectDict({k: v.value for k, v in
                                              step.outputs.parameters.items()
                                              if hasattr(v, "value")}),
                    "artifacts": ObjectDict({k: v.local_path for k, v in
                                             step.outputs.artifacts.items()
                                             if hasattr(v, "local_path")}),
                })})
        tasks = ObjectDict()
        if isinstance(scope, DAG):
            for task in scope:
                tasks[task.name] = ObjectDict({"outputs": ObjectDict({
                    "parameters": ObjectDict({k: v.value for k, v in
                                              task.outputs.parameters.items()
                                              if hasattr(v, "value")}),
                    "artifacts": ObjectDict({k: v.local_path for k, v in
                                             task.outputs.artifacts.items()
                                             if hasattr(v, "local_path")}),
                })})
        variables = {"inputs": inputs, "steps": steps, "tasks": tasks}
        try:
            res = eval(self.expr, variables)
        except Exception:
            raise RuntimeError("Failed to evaluate expression %s "
                               "with variables %s" % (self.expr, variables))
        return res


class AutonamedDict(UserDict):
    def __init__(self, *args, **kwargs):
        self.step = kwargs.get("step", None)
        self.template = kwargs.get("template", None)
        super().__init__(*args)

    def __setitem__(self, key, value):
        assert param_regex.match(key), "Invalid parameter/artifact name '%s':"\
            " %s" % (key, param_errmsg)
        value.name = key
        value.step = self.step
        value.template = self.template
        super().__setitem__(key, value)

    def set_step(self, step):
        self.step = step
        for value in self.values():
            value.step = step

    def set_template(self, template):
        self.template = template
        for value in self.values():
            value.template = template

    def convert_to_graph(self):
        return {k: v.convert_to_graph() for k, v in self.items()
                if not k.startswith("dflow_")}


class InputParameters(AutonamedDict):
    def __setitem__(self, key, value):
        assert isinstance(value, InputParameter)
        super().__setitem__(key, value)


class InputArtifacts(AutonamedDict):
    def __setitem__(self, key, value):
        assert isinstance(value, InputArtifact)
        super().__setitem__(key, value)
        if config["save_path_as_parameter"] and self.template is not None:
            if isinstance(value.source, S3Artifact):
                self.template.inputs.parameters["dflow_%s_path_list" % key] = \
                    InputParameter(value=value.source.path_list)
            else:
                self.template.inputs.parameters["dflow_%s_path_list" % key] = \
                    InputParameter(value=[])
        if config["register_tasks"] and self.template is not None and \
                key[:6] != "dflow_":
            if isinstance(value.source, S3Artifact):
                self.template.inputs.parameters["dflow_%s_urn" % key] = \
                    InputParameter(value=value.source.urn)
            else:
                self.template.inputs.parameters["dflow_%s_urn" % key] = \
                    InputParameter(value="")

    def set_template(self, template):
        super().set_template(template)
        if config["save_path_as_parameter"]:
            for name, art in self.items():
                if isinstance(art.source, S3Artifact):
                    self.template.inputs.parameters["dflow_%s_path_list"
                                                    % name] = InputParameter(
                        value=art.source.path_list)
                else:
                    self.template.inputs.parameters["dflow_%s_path_list"
                                                    % name] = InputParameter(
                        value=[])
        if config["register_tasks"]:
            for name, art in self.items():
                if name[:6] == "dflow_":
                    continue
                if isinstance(art.source, S3Artifact):
                    self.template.inputs.parameters["dflow_%s_urn" % name] = \
                        InputParameter(value=art.source.urn)
                else:
                    self.template.inputs.parameters["dflow_%s_urn" % name] = \
                        InputParameter(value="")


class OutputParameters(AutonamedDict):
    def __setitem__(self, key, value):
        assert isinstance(value, OutputParameter)
        super().__setitem__(key, value)


class OutputArtifacts(AutonamedDict):
    def __setitem__(self, key, value):
        assert isinstance(value, OutputArtifact)
        super().__setitem__(key, value)
        if config["save_path_as_parameter"] and self.template is not None:
            self.template.outputs.parameters["dflow_%s_path_list" % key] = \
                OutputParameter(value=[])
            value.handle_path_list()
        if config["register_tasks"] and self.template is not None:
            self.template.outputs.parameters["dflow_%s_urn" % key] = \
                OutputParameter(value="")
            value.handle_urn()

    def set_template(self, template):
        super().set_template(template)
        if config["save_path_as_parameter"]:
            for name, art in self.items():
                self.template.outputs.parameters["dflow_%s_path_list" % name]\
                    = OutputParameter(value=[])
                art.handle_path_list()
        if config["register_tasks"]:
            for name, art in self.items():
                self.template.outputs.parameters["dflow_%s_urn" % name]\
                    = OutputParameter(value="")
                art.handle_urn()


class ArgoVar:
    is_str = True

    def __init__(self, expr=None, is_str=True):
        self.expr = expr
        self.is_str = is_str

    def __repr__(self):
        return self.expr

    def __getitem__(self, i):
        if config["mode"] == "debug":
            if isinstance(i, str):
                return ArgoVar("%s['%s']" % (self.expr, i))
            elif isinstance(i, int):
                return ArgoVar("%s[%s]" % (self.expr, i))
        if isinstance(i, str):
            item = "jsonpath(%s, '$')['%s']" % (self.expr, i)
        else:
            item = "jsonpath(%s, '$')[%s]" % (self.expr, i)
        return ArgoVar(item, is_str=False)

    def __iter__(self):
        raise TypeError("'ArgoVar' object is not iterable")

    def __eq__(self, other):
        if config["mode"] == "debug":
            if isinstance(other, str):
                return ArgoVar("%s == '%s'" % (self.expr, other))
            else:
                return ArgoVar("%s == %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = other.expr
        elif isinstance(other, str):
            other = "'%s'" % other
        else:
            other = "'%s'" % jsonpickle.dumps(other)
        return ArgoVar("%s == %s" % (self.expr, other))

    def __ne__(self, other):
        if config["mode"] == "debug":
            if isinstance(other, str):
                return ArgoVar("%s != '%s'" % (self.expr, other))
            else:
                return ArgoVar("%s != %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = other.expr
        elif isinstance(other, str):
            other = "'%s'" % other
        else:
            other = "'%s'" % jsonpickle.dumps(other)
        return ArgoVar("%s != %s" % (self.expr, other))

    def __lt__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s < %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) < %s" % (self.expr, other))

    def __le__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s <= %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) <= %s" % (self.expr, other))

    def __gt__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s > %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) > %s" % (self.expr, other))

    def __ge__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s >= %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) >= %s" % (self.expr, other))

    def __add__(self, other):
        if isinstance(other, str):
            return str(self) + other
        if config["mode"] == "debug":
            return ArgoVar("%s + %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) + %s" % (self.expr, other))

    def __sub__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s - %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) - %s" % (self.expr, other))

    def __mul__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s * %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) * %s" % (self.expr, other))

    def __truediv__(self, other):
        if config["mode"] == "debug":
            return ArgoVar("%s / %s" % (self.expr, to_expr(other)))
        if isinstance(other, ArgoVar):
            other = "asFloat(%s)" % other.expr
        return ArgoVar("asFloat(%s) / %s" % (self.expr, other))


class IfExpression(ArgoVar):
    def __init__(
            self,
            _if: Union[str, ArgoVar],
            _then: Union[str, ArgoVar],
            _else: Union[str, ArgoVar],
    ) -> None:
        if isinstance(_if, (InputParameter, OutputParameter)):
            self._if = "%s == 'true'" % _if.expr
        elif isinstance(_if, ArgoVar):
            self._if = _if.expr
        else:
            self._if = _if
        self._then = _then
        self._else = _else

    def __getattr__(self, key):
        # generate attribute expr dynamically because it may change
        if key == "expr":
            return "(%s ? %s : %s)" % (
                self._if, to_expr(self._then), to_expr(self._else))
        return super().__getattr__(key)


def if_expression(
    _if: Union[str, ArgoVar],
    _then: Union[str, ArgoVar],
    _else: Union[str, ArgoVar],
) -> IfExpression:
    """
    Return an if expression in Argo

    Args:
        _if: a bool expression, which may be a comparison of two Argo
            parameters
        _then: value returned if the condition is satisfied
        _else: value returned if the condition is not satisfied
    """
    return IfExpression(_if, _then, _else)


class PVC:
    def __init__(
            self,
            name: str,
            subpath: str,
            size: str = "1Gi",
            storage_class: Optional[str] = None,
            access_modes: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.subpath = subpath
        self.size = size
        self.storage_class = storage_class
        if access_modes is None:
            access_modes = ["ReadWriteOnce"]
        self.access_modes = access_modes


def convert_value_to_str(value):
    if isinstance(value, str):
        return value

    def handle(obj):
        # TODO: Only support dict and list
        if isinstance(obj, (dict, list)):
            for i, v in obj.items() if isinstance(obj, dict) \
                    else enumerate(obj):
                if isinstance(v, ArgoVar):
                    obj[i] = "dflow_placeholder_%s" % len(vars)
                    if (hasattr(v, "type") and v.type == str) or (
                            hasattr(v, "value") and isinstance(v.value, str)):
                        vars.append("\"{{=%s}}\"" % v.expr)
                    elif v.is_str:
                        vars.append("{{=%s}}" % v.expr)
                    else:
                        vars.append("{{=toJson(%s)}}" % v.expr)
                elif isinstance(v, (dict, list)):
                    handle(v)

    vars = []
    handle(value)
    s = jsonpickle.dumps(value)
    for i, var in enumerate(vars):
        s = s.replace("\"dflow_placeholder_%s\"" % i, var)

    return s


class InputParameter(ArgoVar):
    """
    Input parameter for OP template

    Args:
        name: name of the input parameter
        type: parameter type
        value: default value
    """

    def __init__(
            self,
            name: Optional[str] = None,
            step=None,
            template=None,
            type: Optional[Any] = None,
            save_as_artifact: bool = False,
            path: Optional[str] = None,
            source: Union["InputArtifact",
                          "OutputArtifact", S3Artifact] = None,
            **kwargs,
    ) -> None:
        self.name = name
        self.step = step
        self.template = template
        self.type = type
        if "value" in kwargs:
            self.value = kwargs["value"]
        self.save_as_artifact = save_as_artifact
        self.path = path
        self.source = source
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    @classmethod
    def from_dict(cls, d):
        _type = json.loads(d.get("description", "{}")).get("type")
        kwargs = {
            "name": d.get("name", None),
            # for backward compatible
            "type": str if _type in ["str", str(str)] else _type,
        }
        if "value" in d:
            kwargs["value"] = d["value"]
        return cls(**kwargs)

    def __getattr__(self, key):
        from .task import Task
        if key == "expr":
            if self.save_as_artifact:
                if self.name is not None:
                    if self.step is not None:
                        if isinstance(self.step, Task):
                            return "tasks['%s'].inputs.artifacts"\
                                "['dflow_bigpar_%s']" % (
                                    self.step.id, self.name)
                        else:
                            return "steps['%s'].inputs.artifacts["\
                                "'dflow_bigpar_%s']" % (
                                    self.step.id, self.name)
                    return "inputs.artifacts['dflow_bigpar_%s']" % self.name
                return ""
            if self.name is not None:
                if self.step is not None:
                    if isinstance(self.step, Task):
                        return "tasks['%s'].inputs.parameters['%s']" % \
                            (self.step.id, self.name)
                    else:
                        return "steps['%s'].inputs.parameters['%s']" % \
                            (self.step.id, self.name)
                return "inputs.parameters['%s']" % self.name
            return ""
        return super().__getattr__(key)

    def __repr__(self):
        from .task import Task
        if self.save_as_artifact:
            if self.name is not None:
                if self.step is not None:
                    if isinstance(self.step, Task):
                        return "{{tasks.%s.inputs.artifacts.dflow_bigpar_%s}}"\
                            % (self.step.id, self.name)
                    else:
                        return "{{steps.%s.inputs.artifacts.dflow_bigpar_%s}}"\
                            % (self.step.id, self.name)
                return "{{inputs.artifacts.dflow_bigpar_%s}}" % self.name
            return ""
        if self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return "{{tasks.%s.inputs.parameters.%s}}" % (self.step.id,
                                                                  self.name)
                else:
                    return "{{steps.%s.inputs.parameters.%s}}" % (self.step.id,
                                                                  self.name)
            return "{{inputs.parameters.%s}}" % self.name
        return ""

    def convert_to_argo(self):
        description = None
        if self.type is not None:
            description = jsonpickle.dumps({"type": type_to_str(self.type)})

        if self.save_as_artifact:
            if self.source is not None:
                return V1alpha1Artifact(name="dflow_bigpar_" + self.name,
                                        path=self.path, _from=str(self.source))
            elif hasattr(self, "value"):
                if isinstance(self.value, (InputParameter, OutputParameter,
                                           InputArtifact, OutputArtifact)):
                    return V1alpha1Artifact(name="dflow_bigpar_" + self.name,
                                            path=self.path,
                                            _from=str(self.value))
                else:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        path = tmpdir + "/" + self.name
                        with open(path, "w") as f:
                            f.write(jsonpickle.dumps(self.value))
                        key = upload_s3(path)
                        s3 = S3Artifact(key=key)
                    if s3_config["repo_type"] == "s3":
                        return V1alpha1Artifact(
                            name="dflow_bigpar_" + self.name, path=self.path,
                            s3=s3)
                    elif s3_config["repo_type"] == "oss":
                        return V1alpha1Artifact(
                            name="dflow_bigpar_" + self.name, path=self.path,
                            oss=s3.oss())
            else:
                return V1alpha1Artifact(name="dflow_bigpar_" + self.name,
                                        path=self.path)

        if not hasattr(self, "value"):
            return V1alpha1Parameter(name=self.name, description=description)
        elif isinstance(self.value, ArgoVar):
            if self.value.is_str:
                value = "{{=%s}}" % self.value.expr
            else:
                value = "{{=string(%s) == %s ? %s : toJson(%s)}}" % (
                    self.value.expr, self.value.expr, self.value.expr,
                    self.value.expr)
            return V1alpha1Parameter(name=self.name,
                                     value=value,
                                     description=description)
        else:
            return V1alpha1Parameter(name=self.name,
                                     value=convert_value_to_str(self.value),
                                     description=description)

    def convert_to_graph(self):
        g = {
            "name": self.name,
            "type": type_to_str(self.type) if self.type is not None else None,
            "save_as_artifact": self.save_as_artifact,
            "path": self.path,
        }
        if hasattr(self, "value"):
            if isinstance(self.value, (InputParameter, OutputParameter)):
                g["value"] = str(self.value)
            elif isinstance(self.value, ArgoVar):
                if self.value.is_str:
                    g["value"] = "{{=%s}}" % self.value.expr
                else:
                    g["value"] = "{{=string(%s) == %s ? %s : toJson(%s)}}" % (
                        self.value.expr, self.value.expr, self.value.expr,
                        self.value.expr)
            else:
                g["value"] = self.value
        elif self.source is not None:
            if hasattr(self.source, "save_as_artifact"):
                self.source.save_as_artifact = False
            g["value"] = str(self.source) if isinstance(
                self.source, ArgoVar) else self.source
        return g

    @classmethod
    def from_graph(cls, graph):
        return cls(**graph)


class InputArtifact(ArgoVar):
    """
    Input artifact for OP template

    Args:
        path: path where the input artifact is placed in the container
        name: name of the input artifact
        optional: optional artifact or not
        type: artifact type
        source: default source
        archive: regarded as archived file or not
    """

    def __init__(
            self,
            path: Optional[str] = None,
            name: Optional[str] = None,
            step=None,
            template=None,
            optional: bool = False,
            type: Optional[Any] = None,
            source: Union[str, "InputArtifact",
                          "OutputArtifact", S3Artifact] = None,
            mode: Optional[int] = None,
            sub_path: Optional[str] = None,
            archive: str = "default",
            save_as_parameter: bool = False,
            **kwargs,
    ) -> None:
        self.path = path
        self.name = name
        self.step = step
        self.template = template
        self.optional = optional
        self.type = type
        self.source = source
        self._sub_path = None
        self.mode = mode
        self.sp = sub_path
        self.archive = archive
        self.slice = None
        self.parent = None
        self.save_as_parameter = save_as_parameter
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    @classmethod
    def from_dict(cls, d):
        kwargs = {
            "name": d.get("name", None),
            "path": d.get("path", None),
            "optional": d.get("optional", None),
            "mode": d.get("mode", None),
            "sub_path": d.get("subPath", None),
            "archive": None if "none" in d.get("archive", {}) else "tar",
        }
        if "s3" in d:
            kwargs["source"] = S3Artifact(key=d["s3"]["key"], debug_s3=True)
        if "oss" in d:
            kwargs["source"] = S3Artifact(key=d["oss"]["key"], debug_s3=True)
        return cls(**kwargs)

    def __getitem__(self, key):
        art = copy(self)
        art.parent = self
        if art.slice is None:
            art.slice = key
        else:
            art.slice = "%s.%s" % (art.slice, key)
        return art

    def __getattr__(self, key):
        from .task import Task
        if key == "expr":
            if self.name is not None:
                if self.step is not None:
                    if isinstance(self.step, Task):
                        return "tasks['%s'].inputs.artifacts['%s']" % \
                            (self.step.id, self.name)
                    else:
                        return "steps['%s'].inputs.artifacts['%s']" % \
                            (self.step.id, self.name)
                return "inputs.artifacts['%s']" % self.name
            return ""
        return super().__getattr__(key)

    def __repr__(self):
        from .task import Task
        if self.save_as_parameter:
            if self.name is not None:
                suffix = "" if self._sub_path is None else \
                    "/%s" % self._sub_path
                if self.step is not None:
                    if isinstance(self.step, Task):
                        return "{{tasks.%s.inputs.parameters.dflow_art_%s}}%s"\
                            % (self.step.id, self.name, suffix)
                    else:
                        return "{{steps.%s.inputs.parameters.dflow_art_%s}}%s"\
                            % (self.step.id, self.name, suffix)
                return "{{inputs.parameters.dflow_art_%s}}%s" % (self.name,
                                                                 suffix)
            return ""
        if self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return "{{tasks.%s.inputs.artifacts.%s}}" % (self.step.id,
                                                                 self.name)
                else:
                    return "{{steps.%s.inputs.artifacts.%s}}" % (self.step.id,
                                                                 self.name)
            return "{{inputs.artifacts.%s}}" % self.name
        return ""

    def sub_path(self, path):
        artifact = deepcopy(self)
        artifact.parent = self
        if artifact._sub_path is None:
            artifact._sub_path = str(path)
        else:
            artifact._sub_path += "/%s" % path
        return artifact

    def get_path_list_parameter(self):
        return self.template.inputs.parameters["dflow_%s_path_list" %
                                               self.name]

    def get_urn_parameter(self):
        return self.template.inputs.parameters["dflow_%s_urn" % self.name]

    def convert_to_argo(self):
        if self.save_as_parameter:
            if self.source is None:
                return V1alpha1Parameter(name="dflow_art_%s" % self.name)
            elif isinstance(self.source, CustomArtifact):
                if self.source.redirect is not None:
                    return V1alpha1Parameter(name="dflow_art_%s" % self.name,
                                             value=self.source.redirect)
                return V1alpha1Parameter(name="dflow_art_%s" % self.name,
                                         value=self.source.get_urn())
            else:
                return V1alpha1Parameter(name="dflow_art_%s" % self.name,
                                         value=str(self.source))

        archive = None
        if self.archive is None:
            archive = V1alpha1ArchiveStrategy(_none={})
        if self.path in NotAllowedInputArtifactPath:
            raise RuntimeError(
                "Path [%s] is not allowed for input artifact" % self.path)
        if self.source is None:
            return V1alpha1Artifact(name=self.name, path=self.path,
                                    optional=self.optional, mode=self.mode,
                                    archive=archive)
        if isinstance(self.source, (InputArtifact, OutputArtifact)) or (
                isinstance(self.source, str) and self.source.find("{{") != -1):
            sub_path = self.sp if self.sp is not None else \
                getattr(self.source, "_sub_path", None)
            if isinstance(sub_path, ArgoVar):
                sub_path = "{{=%s}}" % sub_path.expr
            return V1alpha1Artifact(name=self.name, path=self.path,
                                    optional=self.optional,
                                    _from=str(self.source), sub_path=sub_path,
                                    mode=self.mode, archive=archive)
        elif isinstance(self.source, S3Artifact):
            if s3_config["repo_type"] == "s3":
                return V1alpha1Artifact(name=self.name, path=self.path,
                                        optional=self.optional, s3=self.source,
                                        sub_path=self.sp, mode=self.mode,
                                        archive=archive)
            else:
                return V1alpha1Artifact(name=self.name, path=self.path,
                                        optional=self.optional,
                                        oss=self.source.oss(),
                                        sub_path=self.sp, mode=self.mode,
                                        archive=archive)
        elif isinstance(self.source, HTTPArtifact):
            return V1alpha1Artifact(name=self.name, path=self.path,
                                    optional=self.optional,
                                    http=V1alpha1HTTPArtifact(
                                        url=self.source.url),
                                    sub_path=self.sp, mode=self.mode,
                                    archive=archive)
        elif isinstance(self.source, str):
            return V1alpha1Artifact(name=self.name, path=self.path,
                                    optional=self.optional,
                                    raw=V1alpha1RawArtifact(data=self.source),
                                    mode=self.mode, archive=archive)
        elif isinstance(self.source, LocalArtifact):
            return {"name": self.name, "path": self.path,
                    "optional": self.optional, "local": {
                        "path": self.source.local_path}}
        else:
            raise RuntimeError(
                "Cannot pass an object of type %s to artifact %s" %
                (type(self.source), self))

    def convert_to_graph(self):
        if hasattr(self.source, "save_as_parameter"):
            self.source.save_as_parameter = False
        if hasattr(self.source, "redirect"):
            self.source.redirect = None

        source = str(self.source) if isinstance(
            self.source, ArgoVar) else self.source
        return {
            "name": self.name,
            "type": type_to_str(self.type) if self.type is not None else None,
            "path": self.path,
            "optional": self.optional,
            "source": source,
            "mode": self.mode,
            "sub_path": self.sp,
            "slice": self.slice,
            "archive": self.archive,
            "save_as_parameter": self.save_as_parameter,
        }

    @classmethod
    def from_graph(cls, graph):
        return cls(**graph)


class OutputParameter(ArgoVar):
    """
    Output parameter for OP template

    Args:
        value_from_path: the value is read from file generated in the container
        value_from_parameter: the value is from another parameter
        name: name of the output parameter
        type: parameter type
        default: default value
        global_name: global name of the parameter within the workflow
        value_from_expression: the value is from an expression
        value: specify value directly
    """

    def __init__(
            self,
            value_from_path: Optional[str] = None,
            value_from_parameter: Union[InputParameter,
                                        "OutputParameter"] = None,
            name: Optional[str] = None,
            step=None,
            template=None,
            type: Optional[Any] = None,
            global_name: Optional[str] = None,
            value_from_expression: Union[str, IfExpression] = None,
            save_as_artifact: bool = False,
            save_both: bool = False,
            **kwargs,
    ) -> None:
        self.value_from_path = value_from_path
        self.name = name
        self.step = step
        self.template = template
        self.type = type
        self.global_name = global_name
        self.value_from_expression = value_from_expression
        self.save_as_artifact = save_as_artifact
        self.save_both = save_both
        if "default" in kwargs:
            self.default = kwargs["default"]
        if "value" in kwargs:
            self.value = kwargs["value"]
        self.value_from_parameter = value_from_parameter

    @classmethod
    def from_dict(cls, d):
        _type = json.loads(d.get("description", "{}")).get("type")
        kwargs = {
            "name": d.get("name", None),
            "value_from_path": d.get("valueFrom", {}).get("path", None),
            # for backward compatible
            "type": str if _type in ["str", str(str)] else _type,
            "global_name": d.get("globalName", None),
            "value_from_expression": d.get("valueFrom", {}).get("expression",
                                                                None),
            "value_from_parameter": d.get("valueFrom", {}).get("parameter",
                                                               None),
        }
        if "valueFrom" in d and "default" in d["valueFrom"]:
            kwargs["default"] = d["valueFrom"]["default"]
        if "value" in d:
            kwargs["value"] = d["value"]
        return cls(**kwargs)

    def expr_as_artifact(self):
        from .task import Task
        if self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return "tasks['%s'].outputs.artifacts"\
                        "['dflow_bigpar_%s']" % (
                            self.step.id, self.name)
                else:
                    return "steps['%s'].outputs.artifacts"\
                        "['dflow_bigpar_%s']" % (
                            self.step.id, self.name)
            return "outputs.artifacts['dflow_bigpar_%s']" % self.name
        return ""

    def expr_as_parameter(self):
        from .task import Task
        if self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return "tasks['%s'].outputs.parameters['%s']" % \
                        (self.step.id, self.name)
                else:
                    return "steps['%s'].outputs.parameters['%s']" % \
                        (self.step.id, self.name)
            return "outputs.parameters['%s']" % self.name
        return ""

    def __getattr__(self, key):
        if key == "expr":
            if self.save_as_artifact:
                return self.expr_as_artifact()
            return self.expr_as_parameter()
        return super().__getattr__(key)

    def __setattr__(self, key, value):
        if key == "value_from_parameter" and \
                isinstance(value, (InputParameter, OutputParameter)):
            if self.save_as_artifact:
                value.save_as_artifact = True
            if value.save_as_artifact:
                self.save_as_artifact = True
            if self.type is None and value.type is not None:
                self.type = value.type
            if value.type is None and self.type is not None:
                value.type = self.type
        if key == "value_from_expression" and isinstance(value, IfExpression) \
                and isinstance(value._then, (InputParameter, OutputParameter)):
            if self.save_as_artifact:
                value._then.save_as_artifact = True
            if value._then.save_as_artifact:
                self.save_as_artifact = True
            if self.type is None and value._then.type is not None:
                self.type = value._then.type
            if value._then.type is None and self.type is not None:
                value._then.type = self.type
        if key == "value_from_expression" and isinstance(value, IfExpression) \
                and isinstance(value._else, (InputParameter, OutputParameter)):
            if self.save_as_artifact:
                value._else.save_as_artifact = True
            if value._else.save_as_artifact:
                self.save_as_artifact = True
            if self.type is None and value._else.type is not None:
                self.type = value._else.type
            if value._else.type is None and self.type is not None:
                value._else.type = self.type
        return super().__setattr__(key, value)

    def repr_as_artifact(self):
        from .task import Task
        if self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return \
                        "{{tasks.%s.outputs.artifacts.dflow_bigpar_%s}}" \
                        % (self.step.id, self.name)
                else:
                    return \
                        "{{steps.%s.outputs.artifacts.dflow_bigpar_%s}}" \
                        % (self.step.id, self.name)
            return "{{outputs.artifacts.dflow_bigpar_%s}}" % self.name
        return ""

    def repr_as_parameter(self):
        from .task import Task
        if self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return "{{tasks.%s.outputs.parameters.%s}}" % (
                        self.step.id, self.name)
                else:
                    return "{{steps.%s.outputs.parameters.%s}}" % (
                        self.step.id, self.name)
            return "{{outputs.parameters.%s}}" % self.name
        return ""

    def __repr__(self):
        if self.save_as_artifact:
            return self.repr_as_artifact()
        return self.repr_as_parameter()

    def convert_to_argo_artifact(self):
        kwargs = {
            "name": "dflow_bigpar_" + self.name,
            "archive": V1alpha1ArchiveStrategy(_none={}),
            "global_name": "dflow_bigpar_" + self.global_name if
            self.global_name is not None else None,
        }
        if self.value_from_path is not None:
            return V1alpha1Artifact(path=self.value_from_path, **kwargs)
        elif self.value_from_parameter is not None:
            return V1alpha1Artifact(
                _from=str(self.value_from_parameter), **kwargs)
        elif self.value_from_expression is not None:
            return V1alpha1Artifact(
                from_expression=str(self.value_from_expression), **kwargs)
        else:
            raise RuntimeError("Not supported.")

    def convert_to_argo_parameter(self):
        description = None
        if self.type is not None:
            description = jsonpickle.dumps({"type": type_to_str(self.type)})

        default = None
        if hasattr(self, "default"):
            default = self.default if isinstance(
                self.default, str) else jsonpickle.dumps(self.default)

        if self.value_from_path is not None:
            return V1alpha1Parameter(
                name=self.name,
                value_from=V1alpha1ValueFrom(
                    path=self.value_from_path,
                    default=default),
                global_name=self.global_name,
                description=description)
        elif self.value_from_parameter is not None:
            return V1alpha1Parameter(
                name=self.name,
                value_from=V1alpha1ValueFrom(
                    # to avoid double rendering
                    parameter=str(self.value_from_parameter).replace(
                        "{{", "").replace("}}", ""),
                    default=default),
                global_name=self.global_name,
                description=description)
        elif self.value_from_expression is not None:
            return V1alpha1Parameter(
                name=self.name,
                value_from=V1alpha1ValueFrom(
                    expression=str(self.value_from_expression),
                    default=default),
                global_name=self.global_name,
                description=description)
        elif hasattr(self, "value"):
            value = self.value if isinstance(
                self.value, str) else jsonpickle.dumps(self.value)
            return V1alpha1Parameter(name=self.name, value=value,
                                     global_name=self.global_name,
                                     description=description)
        else:
            raise RuntimeError("Output parameter %s is not specified" % self)

    def convert_to_argo(self):
        if self.save_as_artifact:
            if self.save_both:
                return self.convert_to_argo_artifact(), \
                    self.convert_to_argo_parameter()
            else:
                return self.convert_to_argo_artifact()
        else:
            return self.convert_to_argo_parameter()

    def convert_to_graph(self):
        g = {
            "name": self.name,
            "value_from_path": self.value_from_path,
            "type": type_to_str(self.type) if self.type is not None else None,
            "global_name": self.global_name,
            "value_from_expression": str(self.value_from_expression)
            if self.value_from_expression is not None else None,
            "save_as_artifact": self.save_as_artifact,
            "save_both": self.save_both,
            "value_from_parameter": None,
        }
        if self.value_from_parameter is not None:
            if hasattr(self.value_from_parameter, "save_as_artifact"):
                self.value_from_parameter.save_as_artifact = False
            g["value_from_parameter"] = str(self.value_from_parameter)
        if hasattr(self, "default"):
            g["default"] = self.default
        if hasattr(self, "value"):
            g["value"] = self.value
        return g

    @classmethod
    def from_graph(cls, graph):
        return cls(**graph)


class OutputArtifact(ArgoVar):
    """
    Output artifact for OP template

    Args:
        path: path of the output artifact in the container
        _from: the artifact is from another artifact
        name: name of the output artifact
        type: artifact type
        save: place to store the output artifact instead of default storage,
            can be a list
        archive: compress format of the artifact, None for no compression
        global_name: global name of the artifact within the workflow
        from_expression: the artifact is from an expression
    """

    def __init__(
            self,
            path: Optional[str] = None,
            _from: Union[InputArtifact, "OutputArtifact"] = None,
            name: Optional[str] = None,
            step=None,
            template=None,
            type: Optional[Any] = None,
            save: List[Union[PVC, S3Artifact]] = None,
            archive: str = "default",
            global_name: Optional[str] = None,
            from_expression: Union[IfExpression, str] = None,
            optional: bool = False,
    ) -> None:
        self.path = path
        self.name = name
        self.step = step
        self.template = template
        self.type = type
        if save is None:
            save = []
        elif not isinstance(save, list):
            save = [save]
        self.save = save
        if archive == "default":
            archive = config["archive_mode"]
        self.archive = archive
        self._sub_path = None
        self.global_name = global_name
        self.from_expression = from_expression
        self.redirect = None
        self._from = _from
        self.slice = None
        self.parent = None
        self.optional = optional

    @classmethod
    def from_dict(cls, d):
        kwargs = {
            "name": d.get("name", None),
            "path": d.get("path", None),
            "archive": None if "none" in d.get("archive", {}) else "tar",
            "global_name": d.get("globalName", None),
            "from_expression": d.get("fromExpression", None),
            "_from": d.get("from", None),
            "optional": d.get("optional", False),
        }
        if "s3" in d:
            kwargs["save"] = [S3Artifact(key=d["s3"]["key"])]
        if "oss" in d:
            kwargs["save"] = [S3Artifact(key=d["oss"]["key"]).oss()]
        return cls(**kwargs)

    def __getitem__(self, key):
        art = copy(self)
        art.parent = self
        if art.slice is None:
            art.slice = key
        else:
            art.slice = "%s.%s" % (art.slice, key)
        return art

    def sub_path(self, path):
        artifact = deepcopy(self)
        artifact.parent = self
        if artifact._sub_path is None:
            artifact._sub_path = str(path)
        else:
            artifact._sub_path += "/%s" % path
        return artifact

    def __getattr__(self, key):
        from .task import Task
        if key == "expr":
            if self.redirect is not None:
                return self.redirect.expr
            if self.global_name is not None:
                return "workflow.outputs.artifacts['%s']" % (self.global_name)
            elif self.name is not None:
                if self.step is not None:
                    if isinstance(self.step, Task):
                        return "tasks['%s'].outputs.artifacts['%s']" % (
                            self.step.id, self.name)
                    else:
                        return "steps['%s'].outputs.artifacts['%s']" % (
                            self.step.id, self.name)
                return "outputs.artifacts['%s']" % self.name
            return ""
        return super().__getattr__(key)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if config["save_path_as_parameter"] and key in ["_from",
                                                        "from_expression"]:
            self.handle_path_list()
        if config["register_tasks"] and key in ["_from", "from_expression"]:
            self.handle_urn()

    def handle_path_list(self):
        if self.template is not None:
            if hasattr(self, "_from") and self._from is not None:
                self.template.outputs.parameters["dflow_%s_path_list" %
                                                 self.name].default = "."
                self.template.outputs.parameters[
                    "dflow_%s_path_list" % self.name].value_from_parameter = \
                    self._from.get_path_list_parameter()
            elif hasattr(self, "from_expression") and self.from_expression is \
                    not None:
                self.template.outputs.parameters["dflow_%s_path_list" %
                                                 self.name].default = "."
                self.template.outputs.parameters[
                    "dflow_%s_path_list" % self.name].value_from_expression = \
                    if_expression(
                    _if=self.from_expression._if,
                    _then=self.from_expression._then.get_path_list_parameter(),
                    _else=self.from_expression._else.get_path_list_parameter(),
                )

    def handle_urn(self):
        if self.template is not None:
            if hasattr(self, "_from") and self._from is not None:
                self.template.outputs.parameters["dflow_%s_urn" %
                                                 self.name].default = ""
                self.template.outputs.parameters[
                    "dflow_%s_urn" % self.name].value_from_parameter = \
                    self._from.get_urn_parameter()
            elif hasattr(self, "from_expression") and self.from_expression is \
                    not None:
                self.template.outputs.parameters["dflow_%s_urn" %
                                                 self.name].default = ""
                self.template.outputs.parameters[
                    "dflow_%s_urn" % self.name].value_from_expression = \
                    if_expression(
                    _if=self.from_expression._if,
                    _then=self.from_expression._then.get_urn_parameter(),
                    _else=self.from_expression._else.get_urn_parameter(),
                )

    def get_path_list_parameter(self):
        return self.step.outputs.parameters["dflow_%s_path_list" % self.name]

    def get_urn_parameter(self):
        return self.step.outputs.parameters["dflow_%s_urn" % self.name]

    def __repr__(self):
        from .task import Task
        if self.redirect is not None:
            return str(self.redirect)
        if self.global_name is not None:
            return "{{workflow.outputs.artifacts.%s}}" % (self.global_name)
        elif self.name is not None:
            if self.step is not None:
                if isinstance(self.step, Task):
                    return "{{tasks.%s.outputs.artifacts.%s}}" % (self.step.id,
                                                                  self.name)
                else:
                    return "{{steps.%s.outputs.artifacts.%s}}" % (self.step.id,
                                                                  self.name)
            return "{{outputs.artifacts.%s}}" % self.name
        return ""

    def pvc(self, size="1Gi", storage_class=None, access_modes=None):
        pvc = PVC("public", randstr(), size, storage_class, access_modes)
        self.save.append(pvc)
        return pvc

    def convert_to_argo(self):
        kwargs = {
            "name": self.name,
            "global_name": self.global_name,
            "optional": self.optional,
        }

        if self.archive is None:
            kwargs["archive"] = V1alpha1ArchiveStrategy(_none={})
        elif self.archive == "tar":
            kwargs["archive"] = None
        else:
            raise RuntimeError("Archive type %s not supported" % self.archive)

        s3 = None
        for save in self.save:
            if isinstance(save, S3Artifact):
                s3 = save

        if s3 is not None:
            if s3_config["repo_type"] == "s3":
                kwargs["s3"] = s3
            elif s3_config["repo_type"] == "oss":
                kwargs["oss"] = s3.oss()

        if self.path is not None:
            return V1alpha1Artifact(path=self.path, **kwargs)
        elif self._from is not None:
            return V1alpha1Artifact(_from=str(self._from), **kwargs)
        elif self.from_expression is not None:
            return V1alpha1Artifact(
                from_expression=str(self.from_expression), **kwargs)
        elif self.optional:
            return V1alpha1Artifact(**kwargs)
        else:
            raise RuntimeError("Output artifact %s is not specified" % self)

    def convert_to_graph(self):
        if hasattr(self._from, "redirect"):
            self._from.redirect = None
        return {
            "name": self.name,
            "path": self.path,
            "type": type_to_str(self.type) if self.type is not None else None,
            "save": self.save,
            "archive": self.archive,
            "global_name": self.global_name,
            "from_expression": str(self.from_expression)
            if self.from_expression is not None else None,
            "_from": str(self._from) if self._from is not None else None,
            "optional": self.optional,
        }

    @classmethod
    def from_graph(cls, graph):
        return cls(**graph)


class Inputs:
    """
    Inputs for OP template

    Args:
        parameters: input parameters
        artifacts: input artifacts
    """

    def __init__(
            self,
            parameters: Dict[str, InputParameter] = None,
            artifacts: Dict[str, InputArtifact] = None,
            step=None,
            template=None,
    ) -> None:
        self.step = step
        self.template = template
        if parameters is not None:
            self.parameters = parameters
        else:
            self.parameters = InputParameters(
                step=self.step, template=self.template)

        if artifacts is not None:
            self.artifacts = artifacts
        else:
            self.artifacts = InputArtifacts(
                step=self.step, template=self.template)

    @classmethod
    def from_dict(cls, d):
        kwargs = {
            "parameters": {par["name"]: InputParameter.from_dict(par)
                           for par in d.get("parameters", [])},
            "artifacts": {art["name"]: InputArtifact.from_dict(art)
                          for art in d.get("artifacts", [])},
        }
        return cls(**kwargs)

    def __setattr__(self, key, value):
        if key == "parameters":
            assert isinstance(value, (dict, UserDict))
            super().__setattr__(key, InputParameters(
                value, step=self.step, template=self.template))
        elif key == "artifacts":
            assert isinstance(value, (dict, UserDict))
            super().__setattr__(key, InputArtifacts(
                value, step=self.step, template=self.template))
        else:
            super().__setattr__(key, value)

    def set_step(self, step):
        self.step = step
        self.parameters.set_step(step)
        self.artifacts.set_step(step)

    def set_template(self, template):
        self.template = template
        self.parameters.set_template(template)
        self.artifacts.set_template(template)

    def convert_to_argo(self):
        parameters = []
        artifacts = []
        for par in self.parameters.values():
            if par.save_as_artifact:
                artifacts.append(par.convert_to_argo())
            else:
                parameters.append(par.convert_to_argo())
        for art in self.artifacts.values():
            if art.save_as_parameter:
                parameters.append(art.convert_to_argo())
            else:
                artifacts.append(art.convert_to_argo())
        return V1alpha1Inputs(parameters=parameters, artifacts=artifacts)

    def convert_to_graph(self):
        return {
            "parameters": self.parameters.convert_to_graph(),
            "artifacts": self.artifacts.convert_to_graph(),
        }

    @classmethod
    def from_graph(cls, graph):
        graph["parameters"] = {
            name: InputParameter.from_graph(par)
            for name, par in graph.get("parameters", {}).items()}
        graph["artifacts"] = {
            name: InputArtifact.from_graph(art)
            for name, art in graph.get("artifacts", {}).items()}
        return cls(**graph)


class Outputs:
    """
    Outputs for OP template

    Args:
        paramters: output parameters
        artifacts: output artifacts
    """

    def __init__(
            self,
            parameters: Dict[str, OutputParameter] = None,
            artifacts: Dict[str, OutputArtifact] = None,
            step=None,
            template=None,
    ) -> None:
        self.step = step
        self.template = template
        if parameters is not None:
            self.parameters = parameters
        else:
            self.parameters = OutputParameters(
                step=self.step, template=self.template)

        if artifacts is not None:
            self.artifacts = artifacts
        else:
            self.artifacts = OutputArtifacts(
                step=self.step, template=self.template)

    @classmethod
    def from_dict(cls, d):
        kwargs = {
            "parameters": {par["name"]: OutputParameter.from_dict(par)
                           for par in d.get("parameters", [])},
            "artifacts": {art["name"]: OutputArtifact.from_dict(art)
                          for art in d.get("artifacts", [])},
        }
        return cls(**kwargs)

    def __setattr__(self, key, value):
        if key == "parameters":
            assert isinstance(value, (dict, UserDict))
            super().__setattr__(key, OutputParameters(
                value, step=self.step, template=self.template))
        elif key == "artifacts":
            assert isinstance(value, (dict, UserDict))
            super().__setattr__(key, OutputArtifacts(
                value, step=self.step, template=self.template))
        else:
            super().__setattr__(key, value)

    def set_step(self, step):
        self.step = step
        self.parameters.set_step(step)
        self.artifacts.set_step(step)

    def set_template(self, template):
        self.template = template
        self.parameters.set_template(template)
        self.artifacts.set_template(template)

    def convert_to_argo(self):
        parameters = []
        artifacts = []
        for par in self.parameters.values():
            if par.save_as_artifact and par.save_both:
                art, par = par.convert_to_argo()
                artifacts.append(art)
                parameters.append(par)
            elif par.save_as_artifact:
                artifacts.append(par.convert_to_argo())
            else:
                parameters.append(par.convert_to_argo())
        for art in self.artifacts.values():
            artifacts.append(art.convert_to_argo())
        return V1alpha1Outputs(parameters=parameters, artifacts=artifacts)

    def convert_to_graph(self):
        return {
            "parameters": self.parameters.convert_to_graph(),
            "artifacts": self.artifacts.convert_to_graph(),
        }

    @classmethod
    def from_graph(cls, graph):
        graph["parameters"] = {
            name: OutputParameter.from_graph(par)
            for name, par in graph.get("parameters", {}).items()}
        graph["artifacts"] = {
            name: OutputArtifact.from_graph(art)
            for name, art in graph.get("artifacts", {}).items()}
        return cls(**graph)
