import inspect
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .. import __path__
from ..common import S3Artifact, jsonpickle
from ..config import config
from ..io import (PVC, InputArtifact, InputParameter, Inputs, OutputArtifact,
                  OutputParameter, Outputs)
from ..op_template import PythonScriptOPTemplate
from ..utils import evalable_repr, randstr, s3_config
from .op import OP, get_source_code
from .opio import Artifact, BigParameter, Parameter

try:
    from argo.workflows.client import (V1Affinity, V1alpha1UserContainer,
                                       V1Toleration, V1Volume, V1VolumeMount)

    from ..client import V1alpha1RetryStrategy
except Exception:
    V1Affinity = object
    V1alpha1UserContainer = object
    V1Toleration = object
    V1Volume = object
    V1VolumeMount = object
upload_packages = []


class Slices:
    """
    Slices specified in PythonOPTemplate

    Args:
        slices: slice pattern
        input_parameter: list of input parameters to be sliced
        input_artifact: list of input artifacts to be sliced
        output_parameter: list of output parameters to be stacked
        output_artifact: list of output artifacts to be stacked
        group_size: number of slices per task/step
        pool_size: for multi slices per task/step, use a multiprocessing pool
            to handle each slice, 1 for serial, -1 for infinity (i.e. equals to
            the number of slices)
        register_first_only: only register first slice when lineage used
        create_dir: create a separate dir for each slice for saving output
            artifacts
        raise_for_group: raise exception finally if any task in the group fails
    """

    def __init__(
            self,
            slices: Optional[str] = None,
            input_parameter: Optional[List[str]] = None,
            input_artifact: Optional[List[str]] = None,
            output_parameter: Optional[List[str]] = None,
            output_artifact: Optional[List[str]] = None,
            sub_path: bool = False,
            group_size: Optional[int] = None,
            shuffle: bool = False,
            random_seed: int = 0,
            pool_size: Optional[int] = None,
            pool_timeout: Optional[int] = None,
            register_first_only: bool = False,
            create_dir: bool = False,
            raise_for_group: bool = False,
    ) -> None:
        self.input_parameter = input_parameter if input_parameter is not \
            None else []
        self.input_artifact = input_artifact if input_artifact is not None \
            else []
        self.output_parameter = output_parameter if output_parameter is not \
            None else []
        self.output_artifact = output_artifact if output_artifact is not \
            None else []
        self.sub_path = sub_path
        if slices is not None:
            self.slices = slices
        elif self.sub_path and group_size is None:
            self.slices = "{{item.order}}"
        else:
            self.slices = "{{item}}"
        self.group_size = group_size
        self.shuffle = shuffle
        self.random_seed = random_seed
        self.pool_size = pool_size
        self.pool_timeout = pool_timeout
        self.register_first_only = register_first_only
        self.create_dir = create_dir
        self.raise_for_group = raise_for_group

    def evalable_repr(self, imports):
        kwargs = {}
        sign = inspect.signature(self.__init__).parameters
        for k, v in self.__dict__.items():
            if k in sign:
                if v == sign[k].default:
                    continue
                if sign[k].default is None and v in [[], {}]:
                    continue
                if k == "slices" and self.sub_path and v == "{{item.order}}":
                    continue
                if k == "slices" and not self.sub_path and v == "{{item}}":
                    continue
                kwargs[k] = v
        imports.add(("dflow.python", "Slices"))
        return "Slices(%s)" % ", ".join(["%s=%s" % (k, evalable_repr(
            v, imports)) for k, v in kwargs.items()])


def handle_packages_script(package_root):
    script = "import os, sys, json\n"
    script += "package_root = r'%s'\n" % package_root
    script += "catalog_dir = os.path.join(package_root, "\
        "'%s')\n" % config['catalog_dir_name']
    script += "if os.path.exists(catalog_dir):\n"
    script += "    for f in os.listdir(catalog_dir):\n"
    script += "        with open(os.path.join(catalog_dir, f), 'r')"\
        " as fd:\n"
    script += "            for item in json.load(fd)['path_list']:\n"
    script += "                path = os.path.join(package_root, "\
        "os.path.dirname(item['dflow_list_item']))\n"
    script += "                sys.path.insert(0, path)\n"
    script += "                os.environ['PYTHONPATH'] = path + ':' + "\
        "os.environ.get('PYTHONPATH', '')\n"
    return script


class PythonOPTemplate(PythonScriptOPTemplate):
    """
    Convert from Python class OP to OP template

    Args:
        op_class: Python class OP
        image: image of the OP template
        command: python executable
        annotations: annotations for the OP template
        labels: labels for the OP template
        node_selector: node selector when scheduling the pod
        tolerations: tolerations of taints when scheduling the pod
        affinity: affinity when scheduling the pod
        input_artifact_slices: a dict specifying input artifacts to use slices
        output_artifact_save: a dict specifying storage of output artifacts
            overriding default storage
        output_artifact_archive: a dict specifying compress format of output
            artifacts, None for no compression
        input_parameter_slices: a dict specifying input parameters to use
            slices
        output_artifact_slices: a dict specifying output artifacts to use
            slices
        output_parameter_slices: a dict specifying output parameters to use
            slices
        output_artifact_global_name: a dict specifying global names of
            output artifacts within the workflow
        slices: use slices to generate parallel steps
        python_packages: local python packages to be uploaded to the OP
        timeout: timeout of the OP template
        retry_on_transient_error: maximum retries on TrasientError
        output_parameter_default: a dict specifying default values for output
            parameters
        output_parameter_global_name: a dict specifying global names of output
            parameters within the workflow
        timeout_as_transient_error: regard timeout as transient error or fatal
            one
        memoize_key: memoized key of the OP template
        volumes: volumes to use in the OP template
        mounts: volumes to mount in the OP template
        image_pull_policy: Always, IfNotPresent, Never
        requests: a dict of resource requests
        limits: a dict of resource limits
        envs: environment variables
        init_containers: init containers before the template runs
        sidecars: sidecar containers
    """

    def __init__(self,
                 op_class: Union[Type[OP], OP],
                 image: Optional[str] = None,
                 command: Union[str, List[str]] = None,
                 annotations: Dict[str, str] = None,
                 labels: Dict[str, str] = None,
                 node_selector: Dict[str, str] = None,
                 tolerations: List[V1Toleration] = None,
                 affinity: V1Affinity = None,
                 output_artifact_save: Dict[str,
                                            List[Union[PVC, S3Artifact]]]
                 = None,
                 output_artifact_archive: Dict[str, Optional[str]] = None,
                 output_parameter_default: Dict[str, Any] = None,
                 input_artifact_prefix: Dict[str, str] = None,
                 input_artifact_slices: Dict[str, str] = None,
                 input_parameter_slices: Dict[str, str] = None,
                 output_artifact_slices: Dict[str, str] = None,
                 output_parameter_slices: Dict[str, str] = None,
                 output_artifact_global_name: Dict[str, str] = None,
                 output_parameter_global_name: Dict[str, str] = None,
                 slices: Optional[Slices] = None,
                 python_packages: Optional[List[os.PathLike]] = None,
                 timeout: Optional[int] = None,
                 retry_on_transient_error: Optional[int] = None,
                 retry_on_failure: Optional[int] = None,
                 retry_on_error: Optional[int] = None,
                 retry_on_failure_and_error: Optional[int] = None,
                 timeout_as_transient_error: bool = False,
                 memoize_key: Optional[str] = None,
                 volumes: Optional[List[V1Volume]] = None,
                 mounts: Optional[List[V1VolumeMount]] = None,
                 image_pull_policy: Optional[str] = None,
                 requests: Dict[str, str] = None,
                 limits: Dict[str, str] = None,
                 upload_dflow: bool = True,
                 envs: Dict[str, str] = None,
                 init_containers: Optional[List[V1alpha1UserContainer]] = None,
                 sidecars: Optional[List[V1alpha1UserContainer]] = None,
                 tmp_root: str = "/tmp",
                 pre_script: str = "",
                 post_script: str = "",
                 success_tag: bool = False,
                 create_slice_dir: bool = False,
                 skip_slice_input: bool = False,
                 ) -> None:
        self.n_parts = {}
        self.keys_of_parts = {}
        self.op_class = op_class
        op = None
        if isinstance(op_class, OP):
            op = op_class
            op_class = op.__class__
        class_name = op_class.__name__
        input_sign = op_class.get_input_sign()
        output_sign = op_class.get_output_sign()
        if output_artifact_save is not None:
            for name, save in output_artifact_save.items():
                output_sign[name].save = save
        if output_artifact_archive is not None:
            for name, archive in output_artifact_archive.items():
                output_sign[name].archive = archive
        if output_artifact_global_name is not None:
            for name, global_name in output_artifact_global_name.items():
                output_sign[name].global_name = global_name
        super().__init__(
            name="%s-%s" % (class_name.replace("_", "-"), randstr()),
            inputs=Inputs(), outputs=Outputs(), volumes=volumes, mounts=mounts,
            requests=requests, limits=limits, envs=envs,
            init_containers=init_containers, sidecars=sidecars, labels=labels,
            annotations=annotations, node_selector=node_selector,
            tolerations=tolerations, affinity=affinity)
        self.pre_script = pre_script
        self.post_script = post_script
        self.success_tag = success_tag
        if timeout is not None:
            self.timeout = "%ss" % timeout
        self.retry_on_transient_error = retry_on_transient_error
        self.retry_on_failure = retry_on_failure
        self.retry_on_error = retry_on_error
        self.retry_on_failure_and_error = retry_on_failure_and_error
        self.timeout_as_transient_error = timeout_as_transient_error
        self.dflow_vars = {}
        self.tmp_root = tmp_root
        for name, sign in input_sign.items():
            if isinstance(sign, Artifact):
                self.inputs.artifacts[name] = InputArtifact(
                    path="%s/inputs/artifacts/" % self.tmp_root + name,
                    optional=sign.optional, type=sign.type,
                    archive=sign.archive)
            elif isinstance(sign, BigParameter):
                if hasattr(sign, "default"):
                    self.inputs.parameters[name] = InputParameter(
                        save_as_artifact=True,
                        path="%s/inputs/parameters/" % self.tmp_root + name,
                        type=sign.type, value=sign.default)
                else:
                    self.inputs.parameters[name] = InputParameter(
                        save_as_artifact=True,
                        path="%s/inputs/parameters/" % self.tmp_root + name,
                        type=sign.type)
            elif isinstance(sign, Parameter):
                if hasattr(sign, "default"):
                    self.inputs.parameters[name] = InputParameter(
                        type=sign.type, value=sign.default)
                else:
                    self.inputs.parameters[name] = InputParameter(
                        type=sign.type)
            else:
                self.inputs.parameters[name] = InputParameter(type=sign)
        for name, sign in output_sign.items():
            if isinstance(sign, Artifact):
                self.outputs.artifacts[name] = OutputArtifact(
                    path="%s/outputs/artifacts/" % self.tmp_root + name,
                    archive=sign.archive, save=sign.save,
                    global_name=sign.global_name, type=sign.type,
                    optional=sign.optional)
                if config["save_path_as_parameter"]:
                    self.outputs.parameters["dflow_%s_path_list" %
                                            name] = OutputParameter(
                        value_from_path="%s/outputs/parameters/"
                        "dflow_%s_path_list" % (self.tmp_root, name),
                        default=[])
                if config["register_tasks"]:
                    self.outputs.parameters["dflow_%s_urn" % name] = \
                        OutputParameter(
                        value_from_path="%s/outputs/parameters/dflow_%s_urn"
                        % (self.tmp_root, name), default="")
            elif isinstance(sign, BigParameter):
                self.outputs.parameters[name] = OutputParameter(
                    save_as_artifact=True,
                    value_from_path="%s/outputs/parameters/" % self.tmp_root
                    + name, type=sign.type)
            elif isinstance(sign, Parameter):
                if hasattr(sign, "default"):
                    self.outputs.parameters[name] = OutputParameter(
                        value_from_path="%s/outputs/parameters/"
                        % self.tmp_root + name, default=sign.default,
                        global_name=sign.global_name, type=sign.type)
                else:
                    self.outputs.parameters[name] = OutputParameter(
                        value_from_path="%s/outputs/parameters/"
                        % self.tmp_root + name, global_name=sign.global_name,
                        type=sign.type)
            else:
                default = None
                if output_parameter_default is not None and name in \
                        output_parameter_default:
                    if sign == str:
                        default = output_parameter_default[name]
                    else:
                        default = jsonpickle.dumps(
                            output_parameter_default[name])
                global_name = None
                if output_parameter_global_name is not None and name in \
                        output_parameter_global_name:
                    global_name = output_parameter_global_name[name]
                self.outputs.parameters[name] = OutputParameter(
                    value_from_path="%s/outputs/parameters/" % self.tmp_root
                    + name, default=default, global_name=global_name,
                    type=sign)

        if python_packages is None:
            python_packages = upload_packages.copy()
        elif isinstance(python_packages, list):
            python_packages = upload_packages + python_packages
        else:
            python_packages = upload_packages + [python_packages]

        self.upload_dflow = upload_dflow
        if upload_dflow:
            python_packages += __path__
            python_packages += jsonpickle.__path__

        self.python_packages = None
        if python_packages:
            self.python_packages = set(python_packages)
            self.inputs.artifacts["dflow_python_packages"] = InputArtifact(
                path="%s/inputs/artifacts/dflow_python_packages"
                % self.tmp_root)

        self.image = image
        self.image_pull_policy = image_pull_policy
        if isinstance(command, str):
            self.command = [command]
        elif command is not None:
            self.command = command
        else:
            self.command = ["python3"]
        self.init_progress = "%s/%s" % (op_class.progress_current,
                                        op_class.progress_total)
        self.memoize_key = memoize_key
        if hasattr(op_class, "func") and config["mode"] == "debug":
            op_class = PicklableFunctionOP(op_class)
            op = op_class

        self.op_class = op_class
        self.input_sign = input_sign
        self.output_sign = output_sign
        self.op = op
        self.input_artifact_prefix = {} if input_artifact_prefix is None \
            else input_artifact_prefix
        self.input_artifact_slices = {} if input_artifact_slices is None \
            else input_artifact_slices
        self.input_parameter_slices = {} if input_parameter_slices is None \
            else input_parameter_slices
        self.output_artifact_slices = {} if output_artifact_slices is None \
            else output_artifact_slices
        self.output_parameter_slices = {} if output_parameter_slices is None \
            else output_parameter_slices
        self.create_slice_dir = create_slice_dir
        self.skip_slice_input = skip_slice_input
        self.set_slices(slices)
        self.download_method = "download"

    def set_slices(self, slices):
        self.slices = slices
        self.input_artifact_slices = {}
        self.input_parameter_slices = {}
        self.output_artifact_slices = {}
        self.output_parameter_slices = {}
        # undo add slices
        for name, sign in self.input_sign.items():
            if isinstance(sign, Artifact):
                if "dflow_%s_sub_path" % name in self.inputs.parameters:
                    del self.inputs.parameters["dflow_%s_sub_path" % name]
                self.inputs.artifacts[name] = InputArtifact(
                    path="%s/inputs/artifacts/" % self.tmp_root + name,
                    optional=sign.optional, type=sign.type,
                    archive=sign.archive)
        if slices is not None:
            self.add_slices(slices)
        else:
            self.render_script()

    def add_slices(self, slices: Slices, layer=0):
        if slices.sub_path and slices.group_size is not None:
            self.inputs.parameters["dflow_ngroups"] = InputParameter()
            slices_slices = "input_slices"
        else:
            slices_slices = slices.slices
        if slices.input_artifact and not slices.sub_path:
            for name in slices.input_artifact:
                self.input_artifact_slices[name] = slices_slices
        if slices.input_parameter:
            for name in slices.input_parameter:
                self.input_parameter_slices[name] = slices_slices
        if slices.output_artifact:
            for name in slices.output_artifact:
                if name in self.output_artifact_slices:
                    s = str(self.output_artifact_slices[name]).strip("'")
                    s += "." + slices_slices
                    self.output_artifact_slices[name] = "'%s'" % s
                else:
                    self.output_artifact_slices[name] = slices_slices
                self.outputs.artifacts[name].archive = None  # no archive
                if slices.create_dir:
                    self.create_slice_dir = True
        if slices.output_parameter:
            for name in slices.output_parameter:
                self.output_parameter_slices[name] = slices_slices

        if slices.sub_path and not slices.group_size:
            for name in slices.input_artifact:
                self.inputs.parameters["dflow_%s_sub_path" %
                                       name] = InputParameter(value=".")
                sign = self.input_sign[name]
                self.inputs.artifacts[name] = InputArtifact(
                    path="%s/inputs/artifacts/%s/{{inputs.parameters."
                    "dflow_%s_sub_path}}" % (self.tmp_root, name, name),
                    optional=sign.optional, type=sign.type)
        self.render_script()

    def set_skip_slice_input(self):
        self.skip_slice_input = True
        self.inputs.parameters["dflow_skip_slice_input"] = InputParameter(
            value=0)

    def render_script(self):
        op_class = self.op_class
        class_name = op_class.__name__
        op = self.op
        input_sign = self.input_sign
        output_sign = self.output_sign
        input_artifact_slices = self.input_artifact_slices
        input_parameter_slices = self.input_parameter_slices
        output_artifact_slices = self.output_artifact_slices
        output_parameter_slices = self.output_parameter_slices

        script = self.pre_script.format(**{"tmp_root": self.tmp_root})
        if self.python_packages:
            script += handle_packages_script(
                "%s/inputs/artifacts/dflow_python_packages" % self.tmp_root)

        script += "import json\n"
        script += "from dflow import config, jsonpickle, s3_config\n"
        script += "config.update(jsonpickle.loads(r'''%s'''))\n" % \
            jsonpickle.dumps(config)
        script += "s3_config.update(jsonpickle.loads(r'''%s'''))\n" % \
            jsonpickle.dumps(s3_config)
        mod = op_class.__module__
        if hasattr(op_class, "_source"):
            script += op_class._source
            mod = "__main__"
        elif mod in ["__main__", "__mp_main__"]:
            try:
                if hasattr(op_class, "func"):
                    script += get_source_code(op_class.func)
                else:
                    script += get_source_code(op_class)
            except Exception:
                logging.info("Failed to get source code of OP, "
                             "use cloudpickle instead", exc_info=True)
                import cloudpickle
                if self.python_packages:
                    self.python_packages.update(cloudpickle.__path__)
                else:
                    self.python_packages = set(cloudpickle.__path__)

                script += "import cloudpickle\n"
                if hasattr(op_class, "func"):
                    script += "from dflow.python import OP\n"
                    script += "%s = OP.function(cloudpickle.loads(%s))\n" % \
                        (class_name, cloudpickle.dumps(op_class.func))
                else:
                    script += "%s = cloudpickle.loads(%s)\n" % \
                        (class_name, cloudpickle.dumps(op_class))

        script += "\nimport os, sys, traceback\n"
        script += "from dflow.python import OPIO, TransientError, FatalError\n"
        script += "from dflow.python.utils import handle_input_artifact," \
                  " handle_input_parameter\n"
        script += "from dflow.python.utils import handle_output_artifact," \
                  " handle_output_parameter, handle_lineage\n"
        if mod not in ["__main__", "__mp_main__"]:
            script += f"from {mod} import {class_name}\n\n"
        if hasattr(op_class, "func"):
            script += "op_obj = %s\n" % class_name
        elif op is None:
            script += "op_obj = %s()\n" % class_name
        else:
            script += "op_obj = jsonpickle.loads(r'''%s''')\n" % \
                jsonpickle.dumps(op)
        script += "op_obj.key = '{{=inputs.parameters.dflow_key}}'\n"
        script += "if op_obj.key.startswith('{'): op_obj.key = None\n"
        script += "op_obj.workflow_name = '{{workflow.name}}'\n"
        script += "if __name__ == '__main__':\n"
        script += "    input = OPIO()\n"
        script += "    input_sign = %s.get_input_sign()\n" % class_name
        script += "    output_sign = %s.get_output_sign()\n" % class_name
        if self.slices is not None and self.slices.pool_size is not None:
            script += "    from dflow.python.utils import try_to_execute\n"
            script += "    from functools import partial\n"
            script += "    try_to_execute = partial(try_to_execute, "\
                "op_obj=op_obj, output_sign=output_sign, cwd=os.getcwd(), "\
                "timeout=%s)\n" % self.slices.pool_timeout
            script += "    from typing import List\n"
            script += "    from pathlib import Path\n"
            for name in self.slices.input_artifact:
                if isinstance(input_sign[name], Artifact):
                    if input_sign[name].type == str:
                        script += "    input_sign['%s'].type = List[str]\n" % \
                            name
                    elif input_sign[name].type == Path:
                        script += "    input_sign['%s'].type = List[Path]\n" %\
                            name
        if any([art.save_as_parameter
                for art in self.inputs.artifacts.values()]):
            script += "    from dflow import CustomArtifact\n"
            script += "    pids = []\n"
            for name in self.inputs.artifacts:
                if self.inputs.artifacts[name].save_as_parameter:
                    script += "    pids.append(CustomArtifact.from_urn('{{"\
                        "inputs.parameters.dflow_art_%s}}').%s('%s', '%s/"\
                        "inputs/artifacts/%s'))\n" % (
                            name, self.download_method, name, self.tmp_root,
                            name)
        if self.slices is not None and self.slices.sub_path and \
                self.slices.group_size is not None:
            for name in self.slices.input_artifact:
                if not self.inputs.artifacts[name].optional:
                    script += "    from dflow.python.utils import "\
                        "get_input_slices\n"
                    script += "    input_slices = get_input_slices('%s', "\
                        "r'%s')\n" % (name, self.tmp_root)
        for name, sign in input_sign.items():
            if isinstance(sign, Artifact):
                slices = self.get_slices(input_artifact_slices, name)
                if self.skip_slice_input and slices is not None:
                    slices = "(None if {{inputs.parameters.dflow_skip_slice_"\
                        "input}} else %s)" % slices
                if "dflow_%s_sub_path" % name in self.inputs.parameters:
                    script += "    input['%s'] = handle_input_artifact('%s', "\
                        "input_sign['%s'], %s, r'%s', '{{inputs.parameters."\
                        "dflow_%s_sub_path}}', None)\n" % (
                            name, name, name, slices, self.tmp_root, name)
                else:
                    script += "    input['%s'] = handle_input_artifact('%s', "\
                        "input_sign['%s'], %s, r'%s', None, n_parts=%s, "\
                        "keys_of_parts=%s, prefix=%s)\n" % (
                            name, name, name, slices, self.tmp_root,
                            self.n_parts.get(name, None),
                            self.keys_of_parts.get(name, None),
                            self.input_artifact_prefix.get(name, None))
            else:
                slices = self.get_slices(input_parameter_slices, name)
                if self.skip_slice_input and slices is not None:
                    slices = "(None if {{inputs.parameters.dflow_skip_slice_"\
                        "input}} else %s)" % slices
                if isinstance(sign, BigParameter):
                    script += "    input['%s'] = handle_input_parameter('%s',"\
                        " '', input_sign['%s'], %s, r'%s')\n" \
                        % (name, name, name, slices, self.tmp_root)
                else:
                    script += "    input['%s'] = handle_input_parameter('%s',"\
                        " r'''{{inputs.parameters.%s}}''', input_sign['%s'], "\
                        "%s, r'%s')\n" % (name, name, name, name, slices,
                                          self.tmp_root)

        script += "    op_obj.tmp_root = '%s'\n" % self.tmp_root
        script += "    op_obj.create_slice_dir = %s\n" % (
            self.create_slice_dir and getattr(self.slices, "pool_size", None)
            is None)
        for name, sign in output_sign.items():
            if isinstance(sign, Artifact):
                slices = self.get_slices(output_artifact_slices, name)
                script += "    op_obj.slices['%s'] = %s\n" % (name, slices)
            else:
                slices = self.get_slices(output_parameter_slices, name)
                script += "    op_obj.slices['%s'] = %s\n" % (name, slices)
        script += "    op_obj.pool_size = %s\n" % getattr(
            self.slices, "pool_size", None)

        script += "    import signal\n"
        script += "    def sigterm_handler(signum, frame):\n"
        script += "        print('Got SIGTERM')\n"
        script += "        raise RuntimeError('Got SIGTERM')\n"
        script += "    signal.signal(signal.SIGTERM, sigterm_handler)\n"

        if self.slices is not None and self.slices.pool_size is not None:
            sliced_inputs = self.slices.input_artifact + \
                self.slices.input_parameter
            script += "    n_slices = None\n"
            for name in sliced_inputs:
                # for optional artifact
                script += "    if input['%s'] is not None:\n" % name
                script += "        if n_slices is None:\n"
                script += "            n_slices = len(input['%s'])\n" % name
                script += "        else:\n"
                script += "            assert len(input['%s']) == n_slices\n" \
                    % name
            script += "    assert n_slices is not None\n"
            script += "    input_list = []\n"
            script += "    from copy import deepcopy\n"
            script += "    for i in range(n_slices):\n"
            script += "        input1 = deepcopy(input)\n"
            for name in sliced_inputs:
                script += "        input1['%s'] = list(input['%s'])[i] if "\
                    "input['%s'] is not None else None\n" % (name, name, name)
            script += "        input_list.append(input1)\n"
            if self.create_slice_dir:
                if self.slices.sub_path and self.slices.group_size is not None:
                    slices = "input_slices"
                else:
                    slices = self.render_slices(self.slices.slices)
                script += "    from dflow.python.utils import slice_to_dir\n"
                script += "    slice_dirs = list(map(slice_to_dir, %s))\n" % \
                    slices
            else:
                script += "    slice_dirs = [None] * n_slices\n"
            if self.slices.pool_size == 1:
                script += "    output_list = []\n"
                script += "    error_list = []\n"
                script += "    for input, slice_dir in zip(input_list, "\
                    "slice_dirs):\n"
                script += "        output, error = try_to_execute(input, "\
                    "slice_dir)\n"
                script += "        output_list.append(output)\n"
                script += "        error_list.append(error)\n"
            else:
                script += "    from multiprocessing import Pool\n"
                if self.slices.pool_size == -1:
                    script += "    pool = Pool(n_slices)\n"
                else:
                    script += "    pool = Pool(%s)\n" % \
                        self.slices.pool_size
                script += "    oe_list = pool.starmap(try_to_execute, "\
                    "zip(input_list, slice_dirs))\n"
                script += "    output_list = [oe[0] for oe in oe_list]\n"
                script += "    error_list = [oe[1] for oe in oe_list]\n"
            sliced_outputs = self.slices.output_artifact + \
                self.slices.output_parameter
            script += "    output = OPIO()\n"
            script += "    for o in output_list:\n"
            script += "        if o is not None:\n"
            script += "            output = o\n"
            for name in sliced_outputs:
                script += "    output['%s'] = [o.get('%s') if o is not None"\
                    " else None for o in output_list]\n" % (name, name)
        else:
            script += "    try:\n"
            script += "        try:\n"
            script += "            output = op_obj.execute(input)\n"
            script += "        except Exception as e:\n"
            script += "            if op_obj.outputs:\n"
            script += "                op_obj.handle_outputs(op_obj.outputs)\n"
            script += "            raise e\n"
            script += "    except TransientError:\n"
            script += "        traceback.print_exc()\n"
            script += "        sys.exit(1)\n"
            script += "    except FatalError:\n"
            script += "        traceback.print_exc()\n"
            script += "        sys.exit(2)\n"

        script += "    op_obj.handle_outputs(output)\n"

        if config["register_tasks"]:
            if self.slices is not None and self.slices.register_first_only:
                if "{{item}}" in self.dflow_vars:
                    var_name = self.dflow_vars["{{item}}"]
                else:
                    var_name = "dflow_var_%s" % len(self.dflow_vars)
                    self.inputs.parameters[var_name] = InputParameter(
                        value="{{item}}")
                    self.dflow_vars["{{item}}"] = var_name
                self.inputs.parameters["dflow_first"] = InputParameter()
                if not hasattr(self, "first_var"):
                    self.first_var = "r'''{{inputs.parameters.dflow_first}}'''"
                script += "    if r'''{{inputs.parameters.%s}}''' == "\
                    "%s:\n" % (var_name, self.first_var)
            else:
                script += "    if True:\n"
            script += "        input_urns = {}\n"
            for name, sign in input_sign.items():
                if isinstance(sign, Artifact):
                    script += "        input_urns['%s'] = '{{inputs."\
                        "parameters.dflow_%s_urn}}'\n" % (name, name)
            script += "        handle_lineage('{{workflow.name}}', "\
                "'{{pod.name}}', op_obj, input_urns, '{{workflow.parameters."\
                "dflow_workflow_urn}}', r'%s')\n" % self.tmp_root

        if self.slices is not None and self.slices.pool_size is not None:
            if self.success_tag:
                script += "    with open('%s/outputs/success_tag', 'w') as f:"\
                    "\n" % self.tmp_root
                script += "        f.write(str(len([e for e in error_list if "\
                    "e is None])))\n"
            if not self.success_tag or config["raise_for_group"] or \
                    self.slices.raise_for_group:
                script += "    try:\n"
                script += "        for error in error_list:\n"
                script += "            if error is not None:\n"
                script += "                raise error\n"
                script += "    except TransientError:\n"
                script += "        sys.exit(1)\n"
                script += "    except FatalError:\n"
                script += "        sys.exit(2)\n"
        else:
            if self.success_tag:
                script += "    with open('%s/outputs/success_tag', 'w') as f:"\
                    "\n" % self.tmp_root
                script += "        f.write('1')\n"

        script += self.post_script.format(**{"tmp_root": self.tmp_root})

        if any([art.save_as_parameter
                for art in self.inputs.artifacts.values()]):
            script += "    import signal\n"
            script += "    [os.killpg(os.getpgid(pid), signal.SIGTERM)"\
                " for pid in pids if pid is not None]\n"

        self.script = script

    def get_slices(self, slices_dict, name):
        slices = None
        if slices_dict is not None:
            slices = self.render_slices(slices_dict.get(name, None))
        return slices

    def render_slices(self, slices=None):
        if not isinstance(slices, str):
            return slices

        i = slices.find("{{item")
        while i >= 0:
            j = slices.find("}}", i+2)
            var = slices[i:j+2]
            if var not in self.dflow_vars:
                var_name = "dflow_var_%s" % len(self.dflow_vars)
                self.inputs.parameters[var_name] = InputParameter(value=var)
                self.dflow_vars[var] = var_name
            else:
                var_name = self.dflow_vars[var]
            slices = slices.replace(var, "{{inputs.parameters.%s}}" % var_name)
            i = slices.find("{{item")
        return slices

    def convert_to_argo(self, memoize_prefix=None, memoize_configmap="dflow"):
        if self.retry_on_transient_error is not None:
            if self.timeout_as_transient_error:
                expr = "asInt(lastRetry.exitCode) != 2"
            else:
                expr = "asInt(lastRetry.exitCode) == 1"
            self.retry_strategy = V1alpha1RetryStrategy(
                limit=self.retry_on_transient_error, expression=expr)
        elif self.retry_on_failure is not None:
            self.retry_strategy = V1alpha1RetryStrategy(
                limit=self.retry_on_failure, retry_policy="OnFailure")
        elif self.retry_on_error is not None:
            self.retry_strategy = V1alpha1RetryStrategy(
                limit=self.retry_on_error, retry_policy="OnError")
        elif self.retry_on_failure_and_error is not None:
            self.retry_strategy = V1alpha1RetryStrategy(
                limit=self.retry_on_failure_and_error, retry_policy="Always")
        return super().convert_to_argo(memoize_prefix, memoize_configmap)

    def convert_to_graph(self):
        g = super().convert_to_graph()
        del g["name"]
        del g["script"]
        del g["inputs"]
        del g["outputs"]
        del g["pvcs"]
        del g["init_progress"]
        del g["retry_strategy"]
        del g["resource"]
        python_packages = []
        for p in self.python_packages:
            if self.upload_dflow and Path(p).name in ["dflow", "jsonpickle"]:
                continue
            python_packages.append(str(p))
        g["type"] = "PythonOPTemplate"
        g["op"] = self.op_class.convert_to_graph()
        g["python_packages"] = python_packages
        g["retry_on_transient_error"] = self.retry_on_transient_error
        g["retry_on_failure"] = self.retry_on_failure
        g["retry_on_error"] = self.retry_on_error
        g["retry_on_failure_and_error"] = self.retry_on_failure_and_error
        g["timeout_as_transient_error"] = self.timeout_as_transient_error
        g["upload_dflow"] = self.upload_dflow
        g["tmp_root"] = self.tmp_root
        g["pre_script"] = self.pre_script
        g["post_script"] = self.post_script
        return g

    @classmethod
    def from_graph(cls, graph):
        assert graph.pop("type") == "PythonOPTemplate"
        graph["op_class"] = OP.from_graph(graph.pop("op"))
        return cls(**graph)


class TransientError(Exception):
    pass


class FatalError(Exception):
    pass


class PicklableFunctionOP:
    def __init__(self, op_class):
        self.__module__ = op_class.__module__
        self.__name__ = op_class.__name__
        if hasattr(op_class, "_source"):
            self._source = op_class._source
            self.__module__ = "__main__"
        elif self.__module__ in ["__main__", "__mp_main__"]:
            self._source = get_source_code(op_class.func)
        self.func = True
