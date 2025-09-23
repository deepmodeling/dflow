import datetime
import json
import logging
import os
import shutil
import tempfile
import time
from collections import UserDict, UserList
from copy import deepcopy
from typing import Any, List, Optional, Union

from .common import jsonpickle
from .config import config, s3_config
from .io import S3Artifact
from .op_template import get_k8s_client
from .utils import download_artifact, get_key, upload_s3

try:
    import kubernetes
except Exception:
    pass

logger = logging.getLogger(__name__)


class ArgoObjectDict(UserDict):
    """
    Generate ArgoObjectDict and ArgoObjectList on initialization rather than
    on __getattr__, otherwise modify a.b.c will not take effect
    """

    def __init__(self, d):
        super().__init__(d)
        for key, value in self.items():
            if isinstance(value, dict):
                self.data[key] = ArgoObjectDict(value)
            elif isinstance(value, list):
                self.data[key] = ArgoObjectList(value)

    def __getattr__(self, key):
        if key == "data":
            return super().__getattr__(key)

        if key in self.data:
            return self.data[key]
        else:
            raise AttributeError(
                "'ArgoObjectDict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        if key == "data":
            return super().__setattr__(key, value)

        self.data[key] = value

    def recover(self):
        return {key: value.recover() if isinstance(value, (ArgoObjectDict,
                                                           ArgoObjectList))
                else value for key, value in self.data.items()}


class ArgoObjectList(UserList):
    def __init__(self, li):
        super().__init__(li)
        for i, value in enumerate(self.data):
            if isinstance(value, dict):
                self.data[i] = ArgoObjectDict(value)
            elif isinstance(value, list):
                self.data[i] = ArgoObjectList(value)

    def recover(self):
        return [value.recover() if isinstance(value, (ArgoObjectDict,
                                                      ArgoObjectList))
                else value for value in self.data]


class ArgoParameter(ArgoObjectDict):
    def __init__(self, par):
        super().__init__(par)

    def __getattr__(self, key):
        if ((key == "value" and "value" not in self.data) or
            (key == "type" and "type" not in self.data)) and \
                hasattr(self, "save_as_artifact"):
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    download_artifact(self, path=tmpdir)
                    fs = os.listdir(tmpdir)
                    assert len(fs) == 1
                    with open(os.path.join(tmpdir, fs[0]), "r") as f:
                        content = jsonpickle.loads(f.read())
                        self.value = content
                except Exception as e:
                    logger.warning("Failed to load parameter value from "
                                   "artifact: %s" % e)
        if key == "value" and hasattr(self, "description") and \
                self.description is not None:
            desc = jsonpickle.loads(self.description)
            # for backward compatible
            if desc["type"] not in ["str", str(str)]:
                try:
                    return jsonpickle.loads(super().__getattr__("value"))
                except Exception as e:
                    logger.warning("Failed to unpickle parameter: %s" % e)
        return super().__getattr__(key)


class ArgoStep(ArgoObjectDict):
    def __init__(self, step, workflow):
        super().__init__(deepcopy(step))
        self.workflow = workflow
        self.pod = None
        self.key = None
        if hasattr(self, "inputs"):
            self.handle_io(self.inputs)
            if hasattr(self.inputs, "parameters") and "dflow_key" in \
                    self.inputs.parameters and self.inputs.parameters[
                        "dflow_key"].value != "":
                self.key = self.inputs.parameters["dflow_key"].value

        if hasattr(self, "outputs"):
            self.handle_io(self.outputs)

    def handle_io(self, io):
        if hasattr(io, "parameters") and \
                isinstance(io.parameters, ArgoObjectList):
            io.parameters = {par.name: ArgoParameter(par)
                             for par in io.parameters}

        if hasattr(io, "artifacts") and \
                isinstance(io.artifacts, ArgoObjectList):
            io.artifacts = {art.name: art for art in io.artifacts}

        self.handle_big_parameters(io)

    def handle_big_parameters(self, io):
        if hasattr(io, "artifacts"):
            for name, art in io.artifacts.items():
                if name[:13] == "dflow_bigpar_":
                    if not hasattr(io, "parameters"):
                        io.parameters = {}
                    if name[13:] not in io.parameters:
                        par = art.copy()
                        par["name"] = name[13:]
                        par["save_as_artifact"] = True
                        io.parameters[name[13:]] = ArgoParameter(par)

    def modify_output_parameter(
            self,
            name: str,
            value: Any,
    ) -> None:
        """
        Modify output parameter of an Argo step

        Args:
            name: parameter name
            value: new value
        """
        if isinstance(value, str):
            self.outputs.parameters[name].value = value
        else:
            self.outputs.parameters[name].value = jsonpickle.dumps(value)

        if hasattr(self.outputs.parameters[name], "save_as_artifact"):
            with tempfile.TemporaryDirectory() as tmpdir:
                path = tmpdir + "/" + name
                with open(path, "w") as f:
                    f.write(jsonpickle.dumps(value))
                if config["mode"] == "debug":
                    path = upload_s3(path, debug_func=shutil.copy)
                    self.outputs.artifacts[
                        "dflow_bigpar_" + name].local_path = path
                    return
                key = upload_s3(path)
                s3 = S3Artifact(key=key)
                if s3_config["repo_type"] == "s3":
                    self.outputs.artifacts["dflow_bigpar_" + name].s3 = \
                        ArgoObjectDict(s3.to_dict())
                elif s3_config["repo_type"] == "oss":
                    self.outputs.artifacts["dflow_bigpar_" + name].oss = \
                        ArgoObjectDict(s3.oss().to_dict())

    def modify_output_artifact(
            self,
            name: str,
            s3: S3Artifact,
    ) -> None:
        """
        Modify output artifact of an Argo step

        Args:
            name: artifact name
            s3: replace the artifact with a s3 object
        """
        if config["mode"] == "debug":
            self.outputs.artifacts[name].local_path = s3.local_path
            return
        assert isinstance(s3, S3Artifact), "must provide a S3Artifact object"
        old_key = get_key(self.outputs.artifacts[name], raise_error=False)
        if s3_config["repo_type"] == "s3":
            self.outputs.artifacts[name].s3 = ArgoObjectDict(s3.to_dict())
        elif s3_config["repo_type"] == "oss":
            self.outputs.artifacts[name].oss = ArgoObjectDict(
                s3.oss().to_dict())
        if s3.key[-4:] == ".tgz" and hasattr(self.outputs.artifacts[name],
                                             "archive"):
            del self.outputs.artifacts[name]["archive"]
        elif s3.key[-4:] != ".tgz" and not hasattr(self.outputs.artifacts[
                name], "archive"):
            self.outputs.artifacts[name]["archive"] = {"none": {}}
        self.outputs.artifacts[name].modified = {"old_key": old_key}

    def retry(self):
        from .workflow import Workflow
        wf = Workflow(id=self.workflow)
        wf.retry_steps([self.id])

    def get_pod(self):
        assert self.type == "Pod"
        wf_name = self.workflow
        node_name = self.name
        template_name = self.templateName
        node_id = self.id
        pod_name = get_pod_name(wf_name, node_name, template_name, node_id)
        with get_k8s_client() as k8s_client:
            core_v1_api = kubernetes.client.CoreV1Api(k8s_client)
            self.pod = core_v1_api.api_client.call_api(
                '/api/v1/namespaces/%s/pods/%s' % (config["namespace"],
                                                   pod_name),
                'GET', response_type='V1Pod',
                header_params=config["http_headers"],
                _return_http_data_only=True)
        return self.pod

    def delete_pod(self):
        assert self.type == "Pod"
        wf_name = self.workflow
        node_name = self.name
        template_name = self.templateName
        node_id = self.id
        pod_name = get_pod_name(wf_name, node_name, template_name, node_id)
        with get_k8s_client() as k8s_client:
            core_v1_api = kubernetes.client.CoreV1Api(k8s_client)
            try:
                core_v1_api.api_client.call_api(
                    '/api/v1/namespaces/%s/pods/%s' % (config["namespace"],
                                                       pod_name),
                    'DELETE', response_type='V1Pod',
                    header_params=config["http_headers"],
                    _return_http_data_only=True)
                logger.info("Deleted pod %s" % pod_name)
            except Exception as e:
                logging.warning("Failed to delete pod %s: %s" % (pod_name, e))
            try:
                while True:
                    core_v1_api.api_client.call_api(
                        '/api/v1/namespaces/%s/pods/%s' % (
                            config["namespace"], pod_name),
                        'GET', response_type='V1Pod',
                        header_params=config["http_headers"],
                        _return_http_data_only=True)
                    logger.info("Waiting pod %s to be deleted..." % pod_name)
                    time.sleep(1)
            except Exception:
                pass

    def get_script(self):
        if self.pod is None:
            self.get_pod()
        main_container = next(filter(lambda c: c.name == "main",
                                     self.pod.spec.containers))
        templ_env = next(filter(lambda e: e.name == "ARGO_TEMPLATE",
                                main_container.env))
        templ = json.loads(templ_env.value)
        return templ["script"]["source"]

    def set_script(self, script):
        if self.pod is None:
            self.get_pod()
        main_container = next(filter(lambda c: c.name == "main",
                                     self.pod.spec.containers))
        templ_env = next(filter(lambda e: e.name == "ARGO_TEMPLATE",
                                main_container.env))
        templ = json.loads(templ_env.value)
        templ["script"]["source"] = script
        templ_env.value = json.dumps(templ)
        init_container = next(filter(lambda c: c.name == "init",
                                     self.pod.spec.init_containers))
        templ_env = next(filter(lambda e: e.name == "ARGO_TEMPLATE",
                                init_container.env))
        templ_env.value = json.dumps(templ)
        wait_container = next(filter(lambda c: c.name == "wait",
                                     self.pod.spec.containers))
        templ_env = next(filter(lambda e: e.name == "ARGO_TEMPLATE",
                                wait_container.env))
        templ_env.value = json.dumps(templ)

    def replay(self):
        if self.pod is None:
            self.get_pod()
        self.pod.metadata.resource_version = None
        self.pod.spec.node_name = None
        self.delete_pod()
        with get_k8s_client() as k8s_client:
            core_v1_api = kubernetes.client.CoreV1Api(k8s_client)
            core_v1_api.api_client.call_api(
                '/api/v1/namespaces/%s/pods' % config["namespace"],
                'POST', body=self.pod, response_type='V1Pod',
                header_params=config["http_headers"],
                _return_http_data_only=True)

    def get_duration(self) -> datetime.timedelta:
        return get_duration(self)


max_k8s_resource_name_length = 253
k8s_naming_hash_length = 10
FNV_32_PRIME = 0x01000193
FNV1_32_INIT = 0x811c9dc5


def get_hash(node_name):
    return fnva(node_name.encode(), FNV1_32_INIT, FNV_32_PRIME, 2**32)


def get_pod_name(wf_name, node_name, template_name, node_id):
    if wf_name == node_name:
        return wf_name
    prefix = "%s-%s" % (wf_name, template_name)
    max_prefix_length = max_k8s_resource_name_length - k8s_naming_hash_length
    if len(prefix) > max_prefix_length - 1:
        prefix = prefix[:max_prefix_length-1]
    hash_val = get_hash(node_name)
    return "%s-%s" % (prefix, hash_val)


def fnva(data, hval_init, fnv_prime, fnv_size):
    """
    Alternative FNV hash algorithm used in FNV-1a.
    """
    assert isinstance(data, bytes)

    hval = hval_init
    for byte in data:
        hval = hval ^ byte
        hval = (hval * fnv_prime) % fnv_size
    return hval


class ArgoWorkflow(ArgoObjectDict):
    def __init__(self, d):
        super().__init__(d)
        self.id = None
        self.uid = None
        if hasattr(self, "metadata") and hasattr(self.metadata, "name"):
            self.id = self.metadata.name
        if hasattr(self, "metadata") and hasattr(self.metadata, "uid"):
            self.uid = self.metadata.uid

    def get_step(
            self,
            name: Union[str, List[str]] = None,
            key: Union[str, List[str]] = None,
            phase: Union[str, List[str]] = None,
            id: Union[str, List[str]] = None,
            type: Union[str, List[str]] = None,
            parent_id: Optional[str] = None,
            sort_by_generation: bool = False,
    ) -> List[ArgoStep]:
        if name is not None and not isinstance(name, list):
            name = [name]
        if key is not None and not isinstance(key, list):
            key = [key]
        if phase is not None and not isinstance(phase, list):
            phase = [phase]
        if id is not None and not isinstance(id, list):
            id = [id]
        if type is not None and not isinstance(type, list):
            type = [type]
        step_list = []
        if hasattr(self.status, "nodes"):
            if parent_id is not None and config["mode"] == "debug":
                nodes = self.get_sub_nodes_debug(parent_id)
            elif parent_id is not None and config["mode"] != "debug":
                nodes = self.get_sub_nodes(parent_id)
            elif sort_by_generation and config["mode"] == "debug":
                nodes = self.get_sub_nodes_debug(self.id)
            elif sort_by_generation and config["mode"] != "debug":
                nodes = self.get_sub_nodes(self.id)
            else:
                nodes = list(self.status.nodes.values())
                nodes.sort(key=lambda x: x.get("startedAt", ""))
            for step in nodes:
                if step["startedAt"] is None:
                    continue
                if name is not None and not match(step["displayName"], name):
                    continue
                if key is not None:
                    step_key = None
                    if "inputs" in step and "parameters" in step["inputs"]:
                        for par in step["inputs"]["parameters"]:
                            if par["name"] == "dflow_key":
                                step_key = par["value"]
                    if step_key not in key:
                        continue
                if phase is not None and not ("phase" in step and
                                              step["phase"] in phase):
                    continue
                if type is not None and not ("type" in step and
                                             step["type"] in type):
                    continue
                if id is not None and step["id"] not in id:
                    continue
                step = ArgoStep(step, self.metadata.name)
                step_list.append(step)
        else:
            return []
        return step_list

    def get_hierarchy(self, node_id, hierarchy=(0,)):
        assert node_id in self.status.nodes
        node = self.status.nodes[node_id]
        sub_nodes = {node_id: hierarchy}
        children = node.get("children", {})
        for order, child_id in children.items():
            if node["type"] == "Steps":
                sub_nodes.update(self.get_hierarchy(
                    child_id, (*hierarchy, int(order.split("-")[0]))))
            else:
                sub_nodes.update(self.get_hierarchy(
                    child_id, (*hierarchy, 0)))
        return sub_nodes

    def get_sub_nodes_debug(self, node_id):
        hierarchy = self.get_hierarchy(node_id)
        if len(hierarchy) == 1:
            return [self.status.nodes[node_id]]
        hierarchy.pop(node_id)
        ids = sorted(hierarchy.keys(), key=lambda x: hierarchy[x])
        return [self.status.nodes[id] for id in ids]

    def get_sub_nodes(self, node_id):
        assert node_id in self.status.nodes
        node = self.status.nodes[node_id]
        if node["type"] not in ["Steps", "DAG"]:
            return [node]
        if node.get("memoizationStatus", {}).get("hit", False):
            return [node]
        sub_nodes = []
        outbound_nodes = node.get("outboundNodes", [])
        children = node.get("children", [])
        # order by generation (BFS)
        current_generation = children
        while len(current_generation) > 0:
            for id in current_generation:
                sub_nodes.append(self.status.nodes[id])
            next_generation = []
            for id in current_generation:
                if id not in outbound_nodes:
                    next_generation += self.status.nodes[id].get(
                        "children", [])
            current_generation = list(set(next_generation))
        return sub_nodes

    def get_duration(self) -> datetime.timedelta:
        return get_duration(self.status)


def get_duration(status) -> datetime.timedelta:
    if status.startedAt is None:
        return datetime.timedelta()
    else:
        ts = datetime.datetime.strptime(status.startedAt,
                                        "%Y-%m-%dT%H:%M:%SZ")
        if status.finishedAt is None:
            tf = datetime.datetime.now()
        else:
            tf = datetime.datetime.strptime(status.finishedAt,
                                            "%Y-%m-%dT%H:%M:%SZ")
        return tf - ts


def match(n, names):
    for name in names:
        if n == name or n.find(name + "(") == 0:
            return True
    return False
