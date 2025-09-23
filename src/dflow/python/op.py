import abc
import base64
import functools
import inspect
import json
import logging
import os
import sys
from abc import ABC
from copy import deepcopy
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Set, Union

from ..argo_objects import ArgoObjectDict
from ..config import config
from ..context_syntax import GLOBAL_CONTEXT
from ..io import (InputArtifact, InputParameter, OutputArtifact,
                  OutputParameter, type_to_str)
from ..utils import dict2list, get_key, randstr, s3_config
from .opio import OPIO, Artifact, BigParameter, OPIOSign, Parameter
from .utils import handle_output_artifact, handle_output_parameter
from .vendor.typeguard import check_type

iwd = os.getcwd()


def get_source_code(o):
    source_lines, start_line = inspect.getsourcelines(o)
    if sys.version_info.minor >= 9:
        source_file = inspect.getsourcefile(o)
    else:
        source_file = os.path.join(iwd, inspect.getsourcefile(o))
    with open(source_file, "r", encoding="utf-8") as fd:
        pre_lines = fd.readlines()[:start_line-1]
    return "".join(pre_lines + source_lines) + "\n"


class OP(ABC):
    """
    Python class OP

    Args:
        progress_total: an int representing total progress
        progress_current: an int representing currenet progress
    """
    progress_total = 1
    progress_current = 0
    key = None
    workflow_name = None
    outputs = {}
    slices = {}
    tmp_root = "/tmp"
    create_slice_dir = False
    pool_size = None

    def __init__(
            self,
            *args,
            **kwargs,
    ) -> None:
        pass

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key in ["progress_total", "progress_current"]:
            with open(os.environ.get("ARGO_PROGRESS_FILE",
                                     "ARGO_PROGRESS_FILE"), "w") as f:
                f.write("%s/%s" % (self.progress_current, self.progress_total))

    @classmethod
    @abc.abstractmethod
    def get_input_sign(cls) -> OPIOSign:
        """Get the signature of the inputs
        """

    @classmethod
    @abc.abstractmethod
    def get_output_sign(cls) -> OPIOSign:
        """Get the signature of the outputs
        """

    def _get_s3_link(self, key):
        if key[-4:] != ".tgz":
            key += "/"
        encoded_key = base64.b64encode(key.encode()).decode()
        return "%s/buckets/%s/browse/%s" % (
            s3_config["console"], s3_config["bucket_name"], encoded_key)

    def get_input_artifact_storage_key(self, name: str) -> str:
        templ = json.loads(os.environ.get("ARGO_TEMPLATE"))
        art = next(filter(lambda x: x["name"] == name,
                          templ["inputs"]["artifacts"]))
        return get_key(ArgoObjectDict(art))

    def get_input_artifact_link(self, name: str) -> str:
        key = self.get_input_artifact_storage_key(name)
        return self._get_s3_link(key)

    def get_output_artifact_storage_key(self, name: str) -> str:
        templ = json.loads(os.environ.get("ARGO_TEMPLATE"))
        art = next(filter(lambda x: x["name"] == name,
                          templ["outputs"]["artifacts"]))
        key = get_key(ArgoObjectDict(art), raise_error=False)
        if key is not None:
            return key

        key = get_key(ArgoObjectDict(templ["archiveLocation"]))
        if "archive" in art and "none" in art["archive"]:
            return "%s/%s" % (key, name)
        else:
            return "%s/%s.tgz" % (key, name)

    def get_output_artifact_link(self, name: str) -> str:
        key = self.get_output_artifact_storage_key(name)
        return self._get_s3_link(key)

    def register_output_artifact(self, name, namespace, dataset_name,
                                 **kwargs):
        if config["lineage"]:
            uri = self.get_output_artifact_storage_key(name)
            config["lineage"].register_artifact(
                namespace=namespace, name=dataset_name, uri=uri, **kwargs)
        else:
            logging.warning("Lineage client not provided")

    @abc.abstractmethod
    def execute(
            self,
            op_in: OPIO,
    ) -> OPIO:
        """Run the OP
        """
        raise NotImplementedError

    @staticmethod
    def exec_sign_check(func):
        @functools.wraps(func)
        def wrapper_exec(self, op_in):
            OP._check_signature(op_in, self.get_input_sign(), True)
            op_out = func(self, op_in)
            OP._check_signature(op_out, self.get_output_sign(), False)
            return op_out

        return wrapper_exec

    @staticmethod
    def _check_signature(
            opio: OPIO,
            sign: OPIOSign,
            is_input: bool,
    ) -> None:
        for ii in sign.keys():
            if ii not in opio.keys():
                if isinstance(sign[ii], Parameter) and hasattr(sign[ii],
                                                               "default"):
                    opio[ii] = sign[ii].default
                elif isinstance(sign[ii], BigParameter) and hasattr(
                        sign[ii], "default"):
                    opio[ii] = sign[ii].default
                elif isinstance(sign[ii], Artifact) and sign[ii].optional:
                    opio[ii] = None
                else:
                    if is_input:
                        raise RuntimeError('key %s declared in the input sign'
                                           ' is not present in the input'
                                           ' passed to the OP' % ii)
                    else:
                        raise RuntimeError('key %s declared in the output sign'
                                           ' is not present in the output'
                                           ' given by the OP' % ii)
        for ii in opio.keys():
            if ii not in sign.keys():
                if is_input:
                    raise RuntimeError(
                        'key %s in the input passed to the OP is not declared'
                        ' in its input sign' % ii)
                else:
                    raise RuntimeError(
                        'key %s in the output given by the OP is not declared'
                        ' in its output sign' % ii)
            io = opio[ii]
            ss = sign[ii]
            if isinstance(ss, Artifact):
                ss = ss.type
                if ss == Dict[str, str]:
                    ss = Dict[str, Union[str, None]]
                elif ss == Dict[str, Path]:
                    ss = Dict[str, Union[Path, None]]
                elif ss == List[str]:
                    ss = List[Union[str, None]]
                elif ss == List[Path]:
                    ss = List[Union[Path, None]]
                elif ss == Set[str]:
                    ss = Set[Union[str, None]]
                elif ss == Set[Path]:
                    ss = Set[Union[Path, None]]
                else:
                    continue
            if isinstance(ss, Parameter):
                ss = ss.type
            # skip type checking if the variable is None
            if io is not None:
                check_type(ii, io, ss)

    @classmethod
    def function(cls, func=None, **kwargs):
        if func is None:
            return partial(cls.function, **kwargs)

        input_sign, output_sign, ret2opio, opio2ret = get_sign_from_func(func)

        class subclass(cls):
            task_kwargs = {}

            @classmethod
            def get_input_sign(cls):
                return deepcopy(input_sign)

            @classmethod
            def get_output_sign(cls):
                return deepcopy(output_sign)

            @OP.exec_sign_check
            def execute(self, op_in):
                op_out = func(**op_in)
                return ret2opio(op_out)

            def use(self, **kwargs):
                op = deepcopy(self)
                op.task_kwargs = kwargs
                return op

            def __call__(self, *args, **op_in):
                input_sign = self.get_input_sign()
                for i, v in enumerate(args):
                    k = list(input_sign)[i]
                    if k in op_in:
                        raise TypeError("%s() got multiple values for argument"
                                        " '%s'" % (func.__name__, k))
                    op_in[k] = v
                if GLOBAL_CONTEXT.in_context:
                    from ..task import Task
                    from .python_op_template import PythonOPTemplate
                    parameters = {k: v for k, v in op_in.items()
                                  if not isinstance(input_sign[k], Artifact)}
                    artifacts = {k: v for k, v in op_in.items()
                                 if isinstance(input_sign[k], Artifact)}
                    name = func.__name__.lower().replace("_", "-") + "-" + \
                        randstr()
                    task = Task(name,
                                template=PythonOPTemplate(self, **kwargs),
                                parameters=parameters, artifacts=artifacts,
                                **self.task_kwargs)
                    op_out = {**task.outputs.parameters,
                              **task.outputs.artifacts}
                    return opio2ret(op_out)
                return self.execute(op_in)

        subclass.func = func
        subclass.__name__ = func.__name__
        subclass.__module__ = func.__module__
        return subclass()

    @classmethod
    def superfunction(cls, func=None, **kwargs):
        if func is None:
            return partial(cls.superfunction, **kwargs)

        input_sign, output_sign, ret2opio, opio2ret = get_sign_from_func(func)

        from ..dag import DAG
        from ..task import Task

        class subclass(DAG):
            task_kwargs = {}

            def use(self, **kwargs):
                op = deepcopy(self)
                op.task_kwargs = kwargs
                return op

            def __call__(self, *args, **op_in):
                for i, v in enumerate(args):
                    k = list(input_sign)[i]
                    if k in op_in:
                        raise TypeError("%s() got multiple values for argument"
                                        " '%s'" % (func.__name__, k))
                    op_in[k] = v
                assert GLOBAL_CONTEXT.in_context
                parameters = {k: op_in[k] for k in self.inputs.parameters
                              if k in op_in}
                artifacts = {k: op_in[k] for k in self.inputs.artifacts
                             if k in op_in}
                name = self.name + "-" + randstr()
                task = Task(name, template=self, parameters=parameters,
                            artifacts=artifacts, **self.task_kwargs)
                op_out = {**task.outputs.parameters, **task.outputs.artifacts}
                return opio2ret(op_out)

        name = func.__name__.lower().replace("_", "-")
        with subclass(name=name, **kwargs) as dag:
            for n, s in input_sign.items():
                if isinstance(s, Artifact):
                    dag.inputs.artifacts[n] = InputArtifact(
                        type=s.type, optional=s.optional)
                else:
                    kw = {}
                    if isinstance(s, (Parameter, BigParameter)):
                        kw["type"] = s.type
                        if hasattr(s, "default"):
                            kw["value"] = s.default
                        if isinstance(s, BigParameter):
                            kw["save_as_artifact"] = True
                    else:
                        kw["type"] = s
                    dag.inputs.parameters[n] = InputParameter(**kw)
            outputs = func(**dag.inputs.parameters, **dag.inputs.artifacts)
            outputs = ret2opio(outputs)
            for n, s in output_sign.items():
                if isinstance(s, Artifact):
                    dag.outputs.artifacts[n] = OutputArtifact(
                        type=s.type, _from=outputs.get(n))
                else:
                    kw = {}
                    if isinstance(s, (Parameter, BigParameter)):
                        kw["type"] = s.type
                        if hasattr(s, "default"):
                            kw["default"] = s.default
                        if isinstance(s, BigParameter):
                            kw["save_as_artifact"] = True
                    else:
                        kw["type"] = s
                    kw["value_from_parameter"] = outputs.get(n)
                    dag.outputs.parameters[n] = OutputParameter(**kw)
        return dag

    @classmethod
    def get_opio_info(cls, opio_sign):
        opio = {}
        for io, sign in opio_sign.items():
            if type(sign) in [Artifact, Parameter, BigParameter]:
                opio[io] = sign
            else:
                opio[io] = type_to_str(sign)
        return opio

    @classmethod
    def get_info(cls):
        res = {}
        name = "%s.%s" % (cls.__module__, cls.__name__)
        res["name"] = name
        res["inputs"] = {k: str(v) for k, v in cls.get_opio_info(
            cls.get_input_sign()).items()}
        res["outputs"] = {k: str(v) for k, v in cls.get_opio_info(
            cls.get_output_sign()).items()}
        if hasattr(cls, "func"):
            res["execute"] = "".join(inspect.getsourcelines(cls.func)[0])
        else:
            res["execute"] = "".join(inspect.getsourcelines(cls.execute)[0])
        return res

    @classmethod
    def convert_to_graph(cls):
        source = None
        try:
            if hasattr(cls, "_source"):
                mod = "__main__"
                source = cls._source
            else:
                mod = str(cls.__module__)
                source = get_source_code(cls.func) if hasattr(
                    cls, "func") else get_source_code(cls)
        except Exception:
            logging.info("Failed to get source code of OP", exc_info=True)
        return {
            "module": mod,
            "name": str(cls.__name__),
            "inputs": cls.get_opio_info(cls.get_input_sign()),
            "outputs": cls.get_opio_info(cls.get_output_sign()),
            "source": source,
        }

    @classmethod
    def from_graph(cls, graph):
        if graph["module"] in ["__main__", "__mp_main__"]:
            exec(graph["source"], globals())
            op = globals()[graph["name"]]
            if isinstance(op, OP):
                op.__class__._source = graph["source"]
            else:
                op._source = graph["source"]
        else:
            mod = import_module(graph["module"])
            op = getattr(mod, graph["name"])
        return op

    def set_output(self, name, value, symlink=True):
        self.outputs[name] = value
        self.handle_outputs({name: value}, symlink=symlink)

    def handle_outputs(self, outputs, symlink=False):
        os.makedirs("%s/outputs/parameters" % self.tmp_root, exist_ok=True)
        os.makedirs("%s/outputs/artifacts" % self.tmp_root, exist_ok=True)
        output_sign = self.get_output_sign()
        for name in outputs:
            sign = output_sign[name]
            if isinstance(sign, Artifact):
                slices = self.slices.get(name)
                if self.pool_size and slices is not None:
                    if sign.type == str:
                        sign.type = List[str]
                    elif sign.type == Path:
                        sign.type = List[Path]
                handle_output_artifact(
                    name, outputs[name], sign, slices, self.tmp_root,
                    self.create_slice_dir and slices, symlink=symlink)
            else:
                slices = self.slices.get(name)
                handle_output_parameter(
                    name, outputs[name], sign, slices, self.tmp_root)


def get_sign_from_func(func):
    signature = inspect.signature(func)
    input_sign = OPIOSign()
    for parameter in signature.parameters.values():
        _type = parameter.annotation
        if _type is inspect._empty:
            _type = Any
        if parameter.default is not inspect._empty:
            if isinstance(_type, Artifact):
                if parameter.default is None:
                    _type.optional = True
            elif isinstance(_type, (Parameter, BigParameter)):
                _type.default = parameter.default
            else:
                _type = Parameter(_type, default=parameter.default)
        input_sign[parameter.name] = _type
    return_type = signature.return_annotation
    if return_type is inspect._empty:
        return_type = None
    output_sign, ret2opio, opio2ret = type2opiosign(return_type)
    return input_sign, output_sign, ret2opio, opio2ret


def type2opiosign(t):
    from typing import Tuple
    try:
        from typing import _GenericAlias as TupleMeta
    except ImportError:
        from typing import TupleMeta
    if isinstance(t, dict):
        return OPIOSign({k: v for k, v in t.items()}), lambda x: x, lambda x: x
    elif hasattr(t, "__annotations__") and issubclass(t, dict):
        return OPIOSign(
            {k: v for k, v in t.__annotations__.items()}), lambda x: x, \
            lambda x: x
    elif hasattr(t, "__annotations__") and issubclass(t, tuple):
        return OPIOSign(
            {k: v for k, v in t.__annotations__.items()}), \
            lambda x: {k: v for k, v in zip(t.__annotations__, x)}, \
            lambda x: tuple(dict2list({list(t.__annotations__).index(k): v
                                       for k, v in x.items()}))
    elif isinstance(t, TupleMeta) and t.__origin__ in [tuple, Tuple]:
        return OPIOSign(
            {"dflow_output_%s" % i: v for i, v in enumerate(t.__args__)}), \
            lambda x: {"dflow_output_%s" % i: v for i, v in enumerate(x)}, \
            lambda x: tuple(dict2list({int(k[13:] if k.startswith(
                "dflow_output_") else k): v for k, v in x.items()}))
    elif t is not None:
        return OPIOSign({"dflow_output": t}), lambda x: {"dflow_output": x}, \
            lambda x: x["dflow_output"]
    else:
        logging.warning(
            'We recommended using return type signature like:'
            '\n'
            "def func()->TypedDict('op', {'x': int, 'y': str})"
            '\nor\n'
            "def func()->NamedTuple('op', [('x', int), ('y', str)])")
        return OPIOSign({}), lambda x: {}, lambda x: None
