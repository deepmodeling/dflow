import json
import logging
import os
import sys
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

from .argo_objects import ArgoStep, ArgoWorkflow, get_hash
from .common import jsonpickle, subdomain_errmsg, subdomain_regex
from .config import config, s3_config
from .context import Context
from .context_syntax import GLOBAL_CONTEXT
from .dag import DAG
from .executor import Executor
from .io import type_to_str
from .op_template import (ContainerOPTemplate, OPTemplate, ScriptOPTemplate,
                          get_k8s_client)
from .step import Step, upload_python_packages
from .steps import Steps
from .task import Task
from .utils import copy_s3, get_key, linktree, randstr, set_key

try:
    import urllib3

    import kubernetes
    urllib3.disable_warnings()
    import yaml
    from argo.workflows.client import (ApiClient, Configuration,
                                       V1alpha1Arguments,
                                       V1alpha1ArtifactRepositoryRef,
                                       V1alpha1Parameter, V1alpha1PodGC,
                                       V1alpha1Workflow,
                                       V1alpha1WorkflowCreateRequest,
                                       V1alpha1WorkflowSpec,
                                       V1LocalObjectReference, V1ObjectMeta,
                                       V1PersistentVolumeClaim,
                                       V1PersistentVolumeClaimSpec,
                                       V1ResourceRequirements,
                                       WorkflowServiceApi)
    from argo.workflows.client.exceptions import ApiException
except Exception:
    pass

logger = logging.getLogger(__name__)


class DockerSecret:
    def __init__(self, registry, username, password, name=None):
        self.registry = registry
        self.username = username
        self.password = password
        if name is None:
            name = "dflow-%s" % randstr()
        self.name = name


class Workflow:
    """
    Workflow

    Args:
        name: the name of the workflow
        steps: steps used as the entrypoint of the workflow, if not provided,
            a empty steps will be used
        dag: dag used as the entrypoint of the workflow
        namespace: k8s namespace
        id: workflow ID in Argo, you can provide it to track an existing
            workflow
        host: URL of the Argo server, will override global config
        token: request the Argo server with the token, will override global
            config
        k8s_config_file: Kubernetes configuration file for accessing API
            server, will override global config
        k8s_api_server: Url of kubernetes API server, will override global
            config
        context: context for the workflow
        annotations: annotations for the workflow
        parallelism: maximum number of running pods for the workflow
        pod_gc_stategy: pod GC provides the ability to delete pods
            automatically without deleting the workflow, pod GC strategy
            must be one of the following:

            * OnPodCompletion - delete pods immediately when pod is completed
                (including errors/failures)
            * OnPodSuccess - delete pods immediately when pod is successful
            * OnWorkflowCompletion - delete pods when workflow is completed
            * OnWorkflowSuccess - delete pods when workflow is successful
        image_pull_secrets: secrets for image registies
        artifact_repo_key: use artifact repository reference by key
        parameters: global input parameters
    """

    def __init__(
            self,
            name: str = "workflow",
            steps: Optional[Steps] = None,
            dag: Optional[DAG] = None,
            namespace: Optional[str] = None,
            id: Optional[str] = None,
            uid: Optional[str] = None,
            host: Optional[str] = None,
            token: Optional[str] = None,
            k8s_config_file: Optional[os.PathLike] = None,
            k8s_api_server: Optional[str] = None,
            context: Optional[Union[Context, Executor]] = None,
            annotations: Dict[str, str] = None,
            labels: Dict[str, str] = None,
            parallelism: Optional[int] = None,
            pod_gc_strategy: Optional[str] = None,
            image_pull_secrets: Optional[Union[
                str, DockerSecret, List[Union[str, DockerSecret]]]] = None,
            artifact_repo_key: Optional[str] = None,
            parameters: Optional[Dict[str, Any]] = None,
            on_exit: Optional[OPTemplate] = None,
    ) -> None:
        self.host = host if host is not None else config["host"]
        self.token = token if token is not None else config["token"]
        self.k8s_config_file = k8s_config_file if k8s_config_file is not None \
            else config["k8s_config_file"]
        self.k8s_api_server = k8s_api_server if k8s_api_server is not None \
            else config["k8s_api_server"]
        self.context = context
        if annotations is None:
            annotations = deepcopy(config["workflow_annotations"])
        self.annotations = annotations
        if labels is None:
            labels = {}
        self.labels = labels
        self.parallelism = parallelism
        self.pod_gc_strategy = pod_gc_strategy
        if image_pull_secrets is not None and not isinstance(
                image_pull_secrets, list):
            image_pull_secrets = [image_pull_secrets]
        self.image_pull_secrets = image_pull_secrets
        self.artifact_repo_key = artifact_repo_key if artifact_repo_key is \
            not None else s3_config["repo_key"]

        api_client = get_argo_api_client(self.host, self.token)
        self.api_instance = WorkflowServiceApi(api_client)

        self.namespace = namespace if namespace is not None else \
            config["namespace"]
        self.id = id
        # alias uid to id if uid not provided
        if uid is None:
            uid = id
        self.uid = uid
        assert subdomain_regex.match(name), "Invalid workflow name '%s': %s"\
            % (name, subdomain_errmsg)
        self.name = name
        if steps is not None:
            assert isinstance(steps, Steps)
            self.entrypoint = steps
        elif dag is not None:
            assert isinstance(dag, DAG)
            self.entrypoint = dag
        else:
            self.entrypoint = None
        self.templates = {}
        self.argo_templates = {}
        self.pvcs = {}
        if parameters is None:
            parameters = {}
        self.parameters = parameters
        self.k8s_client = None
        parse_repo(self.artifact_repo_key, self.namespace,
                   k8s_api_server=self.k8s_api_server, token=self.token,
                   k8s_config_file=self.k8s_config_file)
        self.on_exit = on_exit

    def get_k8s_core_v1_api(self):
        if self.k8s_client is None:
            self.k8s_client = get_k8s_client(self.k8s_api_server, self.token,
                                             self.k8s_config_file)
        return kubernetes.client.CoreV1Api(self.k8s_client)

    def __enter__(self) -> 'Workflow':
        GLOBAL_CONTEXT.in_context = True
        GLOBAL_CONTEXT.current_workflow = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        GLOBAL_CONTEXT.in_context = False
        self.submit()

    def add(
            self,
            step: Union[Step, List[Step], Task, List[Task]],
    ) -> None:
        """
        Add a step or a list of parallel steps to the workflow

        Args:
            step: a step or a list of parallel steps to be added to the
            entrypoint of the workflow
        """
        if self.entrypoint is None:
            if isinstance(step, Task) or (isinstance(step, list) and all(
                    [isinstance(s, Task) for s in step])):
                self.entrypoint = DAG(self.name + "-dag")
            else:
                self.entrypoint = Steps(self.name + "-steps")
        self.entrypoint.add(step)

    def submit(
            self,
            reuse_step: Optional[List[ArgoStep]] = None,
    ) -> ArgoWorkflow:
        """
        Submit the workflow

        Args:
            reuse_step: a list of steps to be reused in the workflow
        """
        if config["mode"] == "debug":
            if self.context is not None:
                assert isinstance(self.context, (Context, Executor))
                self = self.context.render(self)

            if self.id is None:
                while True:
                    self.id = self.name + "-" + randstr()
                    wfdir = os.path.abspath(os.path.join(
                        config["debug_workdir"], self.id))
                    if not os.path.exists(wfdir):
                        os.makedirs(wfdir)
                        break
            else:
                wfdir = os.path.abspath(os.path.join(
                    config["debug_workdir"], self.id))
                if os.path.exists(wfdir):
                    with open(os.path.join(wfdir, "status"), "r") as f:
                        status = f.read()
                    if status == "Succeeded":
                        logger.warning(
                            "Workflow %s has been succeeded" % self.id)
                        return
                    with open(os.path.join(wfdir, "pid"), "r") as f:
                        pid = int(f.read())
                    import psutil
                    try:
                        p = psutil.Process(pid)
                        ps = p.status()
                    except psutil.NoSuchProcess:
                        ps = None
                    logger.warning("Workflow %s process %s is %s" % (
                        self.id, pid, ps))
                    if ps == psutil.STATUS_RUNNING:
                        logger.warning("Do nothing")
                        return
                    logger.warning("Restart workflow %s" % self.id)
                os.makedirs(wfdir, exist_ok=True)

            if reuse_step is not None:
                for step in reuse_step:
                    if step.key is None:
                        continue
                    stepdir = os.path.join(wfdir, step.key)
                    os.makedirs(stepdir, exist_ok=True)
                    with open(os.path.join(stepdir, "name"), "w") as f:
                        f.write(step.displayName)
                    with open(os.path.join(stepdir, "type"), "w") as f:
                        f.write(step.type)
                    with open(os.path.join(stepdir, "phase"), "w") as f:
                        f.write(step.phase)
                    for io in ["inputs", "outputs"]:
                        os.makedirs(os.path.join(stepdir, io, "parameters"),
                                    exist_ok=True)
                        for name, par in step[io].parameters.items():
                            if hasattr(par, "save_as_artifact"):
                                continue
                            with open(os.path.join(stepdir, io, "parameters",
                                                   name), "w") as f:
                                value = par.recover()["value"]
                                if isinstance(value, str):
                                    f.write(value)
                                else:
                                    f.write(jsonpickle.dumps(value))
                            if par.type is not None or hasattr(
                                    par, "globalName"):
                                metadata = {"type": type_to_str(par.type)}
                                if hasattr(par, "globalName"):
                                    metadata["globalName"] = par.globalName
                                os.makedirs(os.path.join(
                                    stepdir, io, "parameters/.dflow"),
                                    exist_ok=True)
                                with open(os.path.join(
                                        stepdir, io, "parameters/.dflow",
                                        name), "w") as f:
                                    f.write(jsonpickle.dumps(metadata))
                            if hasattr(par, "globalName"):
                                os.makedirs(os.path.join(
                                    wfdir, io, "parameters"), exist_ok=True)
                                global_par_path = os.path.join(
                                    wfdir, io, "parameters", par.globalName)
                                if os.path.exists(global_par_path):
                                    os.remove(global_par_path)
                                os.symlink(os.path.join(
                                    stepdir, io, "parameters", name),
                                           global_par_path)

                        os.makedirs(os.path.join(stepdir, io, "artifacts"),
                                    exist_ok=True)
                        if "dflow_group_key" in step.inputs.parameters:
                            key = step.inputs.parameters[
                                "dflow_group_key"].value
                            if not os.path.exists(os.path.join(wfdir, key)) \
                                and not os.path.islink(os.path.join(
                                    wfdir, key)):
                                os.symlink(
                                    os.path.abspath(os.path.join(
                                        config["debug_workdir"], step.workflow,
                                        config["debug_artifact_dir"], key)),
                                    os.path.join(wfdir, key))
                        for name, art in step[io].artifacts.items():
                            if "dflow_group_key" in step.inputs.parameters:
                                key = step.inputs.parameters[
                                    "dflow_group_key"].value
                                if os.path.exists(os.path.join(wfdir, key,
                                                               name)):
                                    if not os.path.samefile(
                                            art.local_path,
                                            os.path.join(wfdir, key, name)):
                                        linktree(
                                            art.local_path,
                                            os.path.join(wfdir, key, name))
                                        os.symlink(
                                            os.path.join(wfdir, key, name),
                                            os.path.join(stepdir, io,
                                                         "artifacts", name))
                                else:
                                    os.symlink(art.local_path, os.path.join(
                                        stepdir, io, "artifacts", name))
                            else:
                                os.symlink(art.local_path, os.path.join(
                                    stepdir, io, "artifacts", name))
                            if hasattr(art, "globalName"):
                                metadata = {"globalName": art.globalName}
                                os.makedirs(os.path.join(
                                    stepdir, io, "artifacts", ".dflow"),
                                    exist_ok=True)
                                with open(os.path.join(
                                        stepdir, io, "artifacts", ".dflow",
                                        name), "w") as f:
                                    f.write(jsonpickle.dumps(metadata))
                                os.makedirs(os.path.join(
                                    wfdir, io, "artifacts"), exist_ok=True)
                                global_art_path = os.path.join(
                                    wfdir, io, "artifacts", art.globalName)
                                if os.path.exists(global_art_path):
                                    os.remove(global_art_path)
                                os.symlink(os.path.join(
                                    stepdir, io, "artifacts", name),
                                           global_art_path)

            cwd = os.getcwd()
            os.chdir(wfdir)
            print("Workflow is running locally (ID: %s)" % self.id)
            with open(os.path.join(wfdir, "status"), "w") as f:
                f.write("Running")
            if config["detach"]:
                pid = os.fork()
                if pid != 0:
                    print("Workflow process ID: %s" % pid)
                    os.chdir(cwd)
                    return ArgoWorkflow({"id": self.id})
                flog = open(os.path.join(wfdir, "log.txt"), "w")
                os.dup2(flog.fileno(), sys.stdout.fileno())
                os.dup2(flog.fileno(), sys.stderr.fileno())
            try:
                with open(os.path.join(wfdir, "pid"), "w") as f:
                    f.write(str(os.getpid()))
                with open(os.path.join(wfdir, "type"), "w") as f:
                    f.write(str(self.entrypoint.__class__.__name__))
                entrypoint = deepcopy(self.entrypoint)
                entrypoint.orig_template = self.entrypoint
                entrypoint.run(self.id, self.context, wfdir)
                with open(os.path.join(wfdir, "status"), "w") as f:
                    f.write("Succeeded")
            except Exception:
                import traceback
                traceback.print_exc()
                with open(os.path.join(wfdir, "status"), "w") as f:
                    f.write("Failed")
            if config["detach"]:
                flog.close()
                exit()
            os.chdir(cwd)
            return ArgoWorkflow({"id": self.id})

        manifest = self.convert_to_argo(reuse_step=reuse_step)

        logger.debug("submit manifest:\n%s" % manifest)
        response = self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s' % self.namespace, 'POST',
            body=V1alpha1WorkflowCreateRequest(workflow=manifest),
            response_type=object,
            header_params=config["http_headers"],
            _return_http_data_only=True)
        workflow = ArgoWorkflow(response)

        self.id = workflow.metadata.name
        self.uid = workflow.metadata.uid
        print("Workflow has been submitted (ID: %s, UID: %s)" % (self.id,
                                                                 self.uid))
        print("Workflow link: %s/workflows/%s/%s" % (self.host, self.namespace,
                                                     self.id))
        return workflow

    def wait(self, interval=1):
        while self.query_status() in ["Pending", "Running"]:
            time.sleep(interval)

    def handle_reused_step(self, step, global_parameters, global_artifacts):
        outputs = {}
        if hasattr(step, "outputs"):
            if hasattr(step.outputs, "exitCode"):
                outputs["exitCode"] = step.outputs.exitCode
            if hasattr(step.outputs, "parameters"):
                outputs["parameters"] = []
                for name, par in step.outputs.parameters.items():
                    if not hasattr(par, "save_as_artifact"):
                        outputs["parameters"].append(par.recover())
                        if hasattr(par, "globalName") and name != \
                                "dflow_global":
                            global_par = par.recover()
                            global_par["name"] = par.globalName
                            global_par.pop("globalName", None)
                            global_parameters[par.globalName] = global_par
            if hasattr(step.outputs, "artifacts"):
                for name, art in step.outputs.artifacts.items():
                    group_key = step.get("inputs", {}).get(
                        "parameters", {}).get("dflow_group_key", {}).get(
                        "value")
                    keys = []
                    if group_key:
                        keys.append(group_key)
                        for k, v in sorted(step.get("inputs", {}).get(
                                "parameters", {}).items()):
                            if k.startswith("dflow_artifact_key_"):
                                keys.append(v.value[v.value.find("/")+1:])
                    art_key = get_key(art, raise_error=False)
                    group_keys = []
                    for i, k in enumerate(keys):
                        if (art_key and art_key.endswith("%s/%s" % (k, name)))\
                            or (getattr(art, "modified", {}).get(
                                "old_key", "").endswith("%s/%s" % (k, name))):
                            group_keys = keys[:i+1]
                    if config["overwrite_reused_artifact"]:
                        for group_key in group_keys:
                            self.handle_reused_artifact(
                                step, name, art, group_key)
                    else:
                        if len(group_keys) > 0:
                            self.handle_reused_artifact_with_copy(
                                step, name, art, group_keys[-1])
                    if hasattr(art, "globalName"):
                        global_art = art.recover()
                        global_art["name"] = art.globalName
                        global_art.pop("globalName", None)
                        global_artifacts[art.globalName] = global_art
                outputs["artifacts"] = [
                    art.recover() for art in step.outputs.artifacts.values()]
        self.memoize_map["%s-%s" % (self.id, step.key)] = {
            "nodeID": step.id,
            "outputs": outputs,
            "creationTimestamp": step.finishedAt,
            "lastHitTimestamp": step.finishedAt
        }

    def handle_reused_artifact(self, step, name, art, group_key):
        art_key = get_key(art, raise_error=False)
        if hasattr(art, "modified"):
            key = art.modified["old_key"]
            logger.debug("copying artifact: %s -> %s" % (art_key, key))
            copy_s3(art_key, key)
            set_key(art, key)
            art_key = key

        art_key_prefix = art_key
        if art_key_prefix.startswith(s3_config["prefix"]):
            art_key_prefix = art_key_prefix[len(s3_config["prefix"]):]
        art_key_prefix = art_key_prefix[:art_key_prefix.find("/")+1]
        art_key_prefix += group_key

        if "%s-init-artifact" % group_key in self.reused_keys:
            return
        memoize_key = "%s-%s-init-artifact" % (self.id, group_key)
        if memoize_key not in self.memoize_map:
            pars = [{
                "name": "dflow_artifact_key",
                "value": art_key_prefix,
            }]
            arts = []
            if "dflow_ngroups" in step.inputs.parameters:
                pars.append({
                    "name": "dflow_ngroups",
                    "value": step.inputs.parameters["dflow_ngroups"].value,
                })
                for k, v in step.inputs.artifacts.items():
                    if hasattr(v, "s3") and hasattr(v.s3, "key"):
                        v_key = v.s3.key
                        storage = "s3"
                    elif hasattr(v, "oss") and hasattr(v.oss, "key"):
                        v_key = v.oss.key
                        storage = "oss"
                    else:
                        continue
                    fields = v_key.split("/")
                    if fields[-2:-1] == [k] and fields[-1].startswith(
                            "group_"):
                        arts.append({
                            "name": k,
                            storage: {"key": "/".join(fields[:-1])},
                            "archive": {"none": {}},
                        })
            if "bohr_job_group_id" in step.inputs.parameters:
                pars.append({
                    "name": "bohr_job_group_id",
                    "value": step.inputs.parameters["bohr_job_group_id"].value,
                })
            self.memoize_map[memoize_key] = {
                "nodeID": "dflow-%s" % randstr(10),
                "outputs": {
                    "parameters": pars,
                    "artifacts": arts,
                },
                "creationTimestamp": step.finishedAt,
                "lastHitTimestamp": step.finishedAt,
            }
        init_step = self.memoize_map[memoize_key]

        init_art = None
        for art in init_step["outputs"]["artifacts"]:
            if art["name"] == name:
                init_art = art
                break
        if not init_art:
            init_art = {"name": name, "archive": {"none": {}}}
            if s3_config["repo_type"] == "s3":
                init_art["s3"] = {"key": art_key}
            elif s3_config["repo_type"] == "oss":
                init_art["oss"] = {"key": s3_config["repo_prefix"] + art_key}
            init_step["outputs"]["artifacts"].append(init_art)

    def handle_reused_artifact_with_copy(self, step, name, art, group_key):
        old_key = get_key(art, raise_error=False)
        if old_key and old_key not in self.copied_keys:
            key = "%s%s/%s/%s" % (
                s3_config["prefix"], self.id, group_key, name)
            logger.debug("copying artifact: %s -> %s" % (old_key, key))
            copy_s3(old_key, key)
            set_key(art, key)
            self.copied_keys.append(old_key)

    def convert_to_argo(self, reuse_step=None):
        self.parents = {}
        if self.context is not None:
            assert isinstance(self.context, (Context, Executor))
            self = self.context.render(self)

        global_parameters = {}
        global_artifacts = {}
        if reuse_step is not None:
            self.reused_keys = [step.key for step in reuse_step
                                if step.key is not None]
            if self.id is None:
                self.id = self.name + "-" + randstr()
            self.copied_keys = []
            self.memoize_map = {}
            key2id = {}
            for step in reuse_step:
                data = {}
                if step.key is None:
                    continue
                node_name = self.id + step.name[len(step.workflow):]
                hash_val = get_hash(node_name)
                new_id = "%s-%s" % (self.id, hash_val)
                key2id[step.key] = new_id
                self.handle_reused_step(step, global_parameters,
                                        global_artifacts)

            for key, step in self.memoize_map.items():
                data = {key: json.dumps(step)}
                config_map = kubernetes.client.V1ConfigMap(
                    data=data, metadata=kubernetes.client.V1ObjectMeta(
                        name="dflow-%s" % key,
                        labels={
                            "workflows.argoproj.io/configmap-type": "Cache",
                        }))
                core_v1_api = self.get_k8s_core_v1_api()
                logger.debug("creating configmap: %s" %
                             config_map.metadata.name)
                core_v1_api.api_client.call_api(
                    '/api/v1/namespaces/%s/configmaps' % self.namespace,
                    'POST', body=config_map, response_type='V1ConfigMap',
                    header_params=config["http_headers"],
                    _return_http_data_only=True)

            self.handle_template(self.entrypoint, memoize_prefix=self.id,
                                 memoize_configmap="dflow")
            if config["save_keys_in_global_outputs"]:
                for key, id in key2id.items():
                    name = "dflow_key_" + key
                    global_parameters[name] = {"name": name, "value": id}
        else:
            self.handle_template(self.entrypoint)

        argo_pvcs = []
        for pvc in self.pvcs.values():
            argo_pvcs.append(V1PersistentVolumeClaim(
                metadata=V1ObjectMeta(name=pvc.name),
                spec=V1PersistentVolumeClaimSpec(
                    storage_class_name=pvc.storage_class,
                    access_modes=pvc.access_modes,
                    resources=V1ResourceRequirements(
                        requests={"storage": pvc.size}
                    )
                )
            ))

        if self.id is not None:
            metadata = V1ObjectMeta(
                name=self.id, annotations=self.annotations, labels=self.labels)
        else:
            metadata = V1ObjectMeta(
                generate_name=self.name + '-', annotations=self.annotations,
                labels=self.labels)

        if self.image_pull_secrets is not None:
            for i, s in enumerate(self.image_pull_secrets):
                if isinstance(s, DockerSecret):
                    data = {".dockerconfigjson": json.dumps({
                        "auths": {s.registry: {
                            "username": s.username, "password": s.password}}})}
                    secret = kubernetes.client.V1Secret(
                        string_data=data,
                        metadata=kubernetes.client.V1ObjectMeta(name=s.name),
                        type="kubernetes.io/dockerconfigjson")
                    core_v1_api = self.get_k8s_core_v1_api()
                    core_v1_api.api_client.call_api(
                        '/api/v1/namespaces/%s/secrets' % self.namespace,
                        'POST', body=secret, response_type='V1Secret',
                        header_params=config["http_headers"],
                        _return_http_data_only=True)
                    self.image_pull_secrets[i] = V1LocalObjectReference(s.name)

        if config["register_tasks"]:
            workflow_urn = config["lineage"].register_workflow(self.name)
            self.parameters["dflow_workflow_urn"] = workflow_urn

        if self.on_exit is not None:
            if hasattr(self.on_exit, "python_packages") and \
                    self.on_exit.python_packages:
                artifact = upload_python_packages(self.on_exit.python_packages)
                self.on_exit.inputs.artifacts[
                    "dflow_python_packages"].source = artifact
            self.handle_template(self.on_exit)

        self.deduplicate_templates()
        return V1alpha1Workflow(
            metadata=metadata,
            spec=V1alpha1WorkflowSpec(
                arguments=V1alpha1Arguments(
                    parameters=[V1alpha1Parameter(
                        name=k, value=v if isinstance(v, str) else
                        jsonpickle.dumps(v)) for k, v in
                        self.parameters.items()]),
                service_account_name='argo',
                entrypoint=self.entrypoint.name,
                templates=list(self.argo_templates.values()),
                parallelism=self.parallelism,
                volume_claim_templates=argo_pvcs,
                pod_gc=V1alpha1PodGC(strategy=self.pod_gc_strategy),
                image_pull_secrets=self.image_pull_secrets,
                artifact_repository_ref=None if self.artifact_repo_key is None
                else V1alpha1ArtifactRepositoryRef(key=self.artifact_repo_key),
                on_exit=self.on_exit.name if self.on_exit is not None else None
            ),
            status={"outputs": {"parameters": list(global_parameters.values()),
                                "artifacts": list(global_artifacts.values())}})

    def deduplicate_templates(self):
        logger.debug("before deduplication: %s" % len(self.argo_templates))
        modified = self.argo_templates
        deduplicated = {}
        while modified:
            modified_name = set()
            for n1, t1 in modified.items():
                duplicate = False
                for n2, t2 in deduplicated.items():
                    t1.name = n2
                    if t1 == t2:
                        duplicate = True
                        logger.debug("template %s == %s, remove %s" % (
                            n1, n2, n1))
                        for parent in self.parents.get(n1, []):
                            if parent.steps:
                                for step in parent.steps:
                                    for ps in step:
                                        if ps.template == n1:
                                            ps.template = n2
                                        if ps.hooks:
                                            for hook in ps.hooks.values():
                                                if hook.template == n1:
                                                    hook.template = n2
                            elif parent.dag:
                                for task in parent.dag.tasks:
                                    if task.template == n1:
                                        task.template = n2
                                    if task.hooks:
                                        for hook in task.hooks.values():
                                            if hook.template == n1:
                                                hook.template = n2
                            self.parents[n2] = self.parents.get(n2, []) + [
                                parent]
                            modified_name.add(parent.name)
                        break
                if not duplicate:
                    t1.name = n1
                    deduplicated[n1] = t1
            self.argo_templates = deduplicated
            modified = {k: v for k, v in self.argo_templates.items()
                        if k in modified_name}
            deduplicated = {k: v for k, v in self.argo_templates.items()
                            if k not in modified_name}
        logger.debug("after deduplication: %s" % len(self.argo_templates))

    def to_dict(self):
        return self.api_instance.api_client.sanitize_for_serialization(
            self.convert_to_argo())

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), **kwargs)

    def to_yaml(self, **kwargs):
        return yaml.dump(self.to_dict(), **kwargs)

    @classmethod
    def from_json(cls, s):
        return cls.from_dict(json.loads(s))

    @classmethod
    def from_yaml(cls, s):
        return cls.from_dict(yaml.full_load(s))

    @classmethod
    def from_dict(cls, d):
        kwargs = {
            "name": d.get("metadata", {}).get(
                "generateName", "workflow").strip("-"),
            "namespace": d.get("metadata", {}).get("namespace", None),
            "id": d.get("metadata", {}).get("name", None),
            "annotations": d.get("metadata", {}).get("annotations", None),
            "labels": d.get("metadata", {}).get("labels", None),
            "parallelism": d.get("spec", {}).get("parallelism", None),
            "pod_gc_strategy": d.get("spec", {}).get("podGC", {}).get(
                "strategy", None),
            "artifact_repo_key": d.get("spec", {}).get(
                "artifact_repository_ref", {}).get("key", None),
            "image_pull_secrets": d.get("spec", {}).get("imagePullSecrets",
                                                        None),
            "parameters": {par["name"]: par["value"] for par in d.get(
                "spec", {}).get("arguments", {}).get("parameters", [])}
        }
        templates = {}
        for template in d["spec"]["templates"]:
            name = template["name"]
            if "script" in template:
                templates[name] = ScriptOPTemplate()
            elif "steps" in template:
                templates[name] = Steps()
            elif "dag" in template:
                templates[name] = DAG()
            elif "container" in template:
                templates[name] = ContainerOPTemplate()
            templates[name].__dict__.update(
                OPTemplate.from_dict(template).__dict__)
        for template in d["spec"]["templates"]:
            name = template["name"]
            if "script" in template:
                templates[name].__dict__.update(
                    ScriptOPTemplate.from_dict(template).__dict__)
            elif "steps" in template:
                templates[name].__dict__.update(
                    Steps.from_dict(template, templates).__dict__)
            elif "dag" in template:
                templates[name].__dict__.update(
                    DAG.from_dict(template, templates).__dict__)
            elif "container" in template:
                templates[name].__dict__.update(
                    ContainerOPTemplate.from_dict(template).__dict__)
        entrypoint = templates[d["spec"]["entrypoint"]]
        if isinstance(entrypoint, ScriptOPTemplate):
            kwargs["steps"] = Steps()
            step = Step("main", entrypoint,
                        parameters=kwargs.pop("parameters"))
            kwargs["steps"].add(step)
        elif isinstance(entrypoint, Steps):
            kwargs["steps"] = entrypoint
        elif isinstance(entrypoint, DAG):
            kwargs["dag"] = entrypoint
        engine = d.get("metadata", {}).get("annotations", {}).get(
            "workflow.dp.tech/container_engine")
        docker = "docker" if engine == "docker" else None
        singularity = "singularity" if engine == "singularity" else None
        podman = "podman" if engine == "podman" else None
        if d.get("metadata", {}).get("annotations", {}).get(
                "workflow.dp.tech/executor") == "dispatcher":
            host = kwargs["annotations"].get("workflow.dp.tech/host")
            port = int(kwargs["annotations"].get("workflow.dp.tech/port", 22))
            username = kwargs["annotations"].get(
                "workflow.dp.tech/username", "root")
            password = kwargs["annotations"].get("workflow.dp.tech/password")
            queue_name = kwargs["annotations"].get(
                "workflow.dp.tech/queue_name")
            extras = kwargs["annotations"].get("workflow.dp.tech/extras")
            extras = json.loads(extras) if extras else {}
            machine = extras.get("machine", None)
            resources = extras.get("resources", None)
            task = extras.get("task", None)
            clean = extras.get("clean", True)
            from .plugins.dispatcher import DispatcherExecutor
            kwargs["context"] = DispatcherExecutor(
                host, queue_name, port, username, password,
                machine_dict=machine, resources_dict=resources,
                task_dict=task, docker_executable=docker,
                singularity_executable=singularity, podman_executable=podman,
                clean=clean)
        elif engine:
            from .executor import ContainerExecutor
            kwargs["context"] = ContainerExecutor(docker, singularity, podman)
        return cls(**kwargs)

    def handle_template(self, template, memoize_prefix=None,
                        memoize_configmap="dflow"):
        if template.name in self.templates:
            assert template == self.templates[template.name], \
                "Duplication of template name: %s" % template.name
        else:
            logger.debug("handle template %s" % template.name)
            self.templates[template.name] = template
            # if the template is steps or dag, handle involved templates
            if isinstance(template, (Steps, DAG)):
                # breadth first algorithm
                argo_template, templates = template.convert_to_argo(
                    memoize_prefix, memoize_configmap, self.context)
                self.argo_templates[template.name] = argo_template
                for t in templates:
                    self.parents[t.name] = self.parents.get(t.name, []) + [
                        argo_template]
                    self.handle_template(t, memoize_prefix, memoize_configmap)
            else:
                self.argo_templates[template.name] = template.convert_to_argo(
                    memoize_prefix, memoize_configmap)
                for pvc in template.pvcs:
                    if pvc.name not in self.pvcs:
                        self.pvcs[pvc.name] = pvc

    def get_graph_templates(self, template, graph_templates=None):
        if graph_templates is None:
            graph_templates = {}
        if template.name not in graph_templates:
            if isinstance(template, (Steps, DAG)):
                graph_template, templates = template.convert_to_graph()
                graph_templates[template.name] = graph_template
                for t in templates:
                    self.get_graph_templates(t, graph_templates)
            else:
                graph_templates[template.name] = template.convert_to_graph()
        return graph_templates

    def to_graph(self):
        graph_templates = self.get_graph_templates(self.entrypoint)
        g = {
            "name": self.name,
            "namespace": self.namespace,
            "id": self.id,
            "context": self.context,
            "annotations": self.annotations,
            "labels": self.labels,
            "parallelism": self.parallelism,
            "pod_gc_strategy": self.pod_gc_strategy,
            "artifact_repo_key": self.artifact_repo_key,
            "image_pull_secrets": self.image_pull_secrets,
            "parameters": self.parameters,
            "entrypoint": self.entrypoint.name,
            "templates": graph_templates,
        }
        return json.loads(jsonpickle.dumps(g, make_refs=False))

    def to_graph_json(self, **kwargs):
        return json.dumps(self.to_graph(), **kwargs)

    def to_graph_yaml(self, **kwargs):
        return yaml.dump(self.to_graph(), **kwargs)

    @classmethod
    def from_graph(cls, graph):
        from .python import PythonOPTemplate

        graph = jsonpickle.loads(json.dumps(graph))
        templates = {}
        for name, template in list(graph["templates"].items()):
            if template["type"] == "PythonOPTemplate":
                templates[name] = PythonOPTemplate.from_graph(template)
                del graph["templates"][name]
            elif template["type"] == "ScriptOPTemplate":
                templates[name] = ScriptOPTemplate.from_graph(template)
                del graph["templates"][name]

        while len(graph["templates"]) > 0:
            update = False
            for name, template in list(graph["templates"].items()):
                if template["type"] == "Steps":
                    if all([all([
                        ps["template"] in templates or ps["template"] == name
                            for ps in s]) for s in template["steps"]]):
                        templates[name] = Steps.from_graph(template, templates)
                        del graph["templates"][name]
                        update = True
                elif template["type"] == "DAG":
                    if all([
                        t["template"] in templates or t["template"] == name
                            for t in template["tasks"]]):
                        templates[name] = DAG.from_graph(template, templates)
                        del graph["templates"][name]
                        update = True
            assert update, "Failed to resolve templates: %s" % list(
                graph["templates"])

        del graph["templates"]
        entrypoint = templates[graph.pop("entrypoint")]
        if isinstance(entrypoint, Steps):
            graph["steps"] = entrypoint
        elif isinstance(entrypoint, DAG):
            graph["dag"] = entrypoint
        return cls(**graph)

    @classmethod
    def from_graph_json(cls, j, **kwargs):
        return cls.from_graph(json.loads(j, **kwargs))

    @classmethod
    def from_graph_yaml(cls, y, **kwargs):
        return cls.from_graph(yaml.full_load(y, **kwargs))

    def query(
            self,
            fields: Optional[List[str]] = None,
            retry: int = 3,
    ) -> ArgoWorkflow:
        """
        Query the workflow from Argo
        If fields is not provided, full information of all steps will be
        returned [O(n)]

        Args:
            fields: fields of the workflow to be returned
        Returns:
            an ArgoWorkflow object
        """
        if config["mode"] == "debug":
            nodes = {}
            for step in self.query_step():
                step.inputs.parameters = list(step.inputs.parameters.values())
                step.inputs.artifacts = list(step.inputs.artifacts.values())
                step.outputs.parameters = list(
                    step.outputs.parameters.values())
                step.outputs.artifacts = list(step.outputs.artifacts.values())
                nodes[step.id] = step.recover()
            wfdir = os.path.join(config["debug_workdir"], self.id)
            _type = "Steps"
            if os.path.exists(os.path.join(wfdir, "type")):
                with open(os.path.join(wfdir, "type"), "r") as f:
                    _type = f.read()
            phase = "Pending"
            if os.path.exists(os.path.join(wfdir, "status")):
                with open(os.path.join(wfdir, "status"), "r") as f:
                    phase = f.read()
            children = {}
            if os.path.exists(os.path.join(wfdir, "children")):
                with open(os.path.join(wfdir, "children"), "r") as f:
                    children = json.load(f)
            nodes[self.id] = {
                "workflow": self.id,
                "displayName": self.id,
                "key": self.id,
                "id": self.id,
                "startedAt": os.path.getmtime(wfdir),
                "phase": phase,
                "type": _type,
                "children": children,
            }
            outputs = self.query_global_outputs()
            if outputs is not None:
                outputs.parameters = list(outputs.parameters.values())
                outputs.artifacts = list(outputs.artifacts.values())
                outputs = outputs.recover()
            response = {
                "metadata": {
                    "name": self.id,
                },
                "status": {
                    "phase": self.query_status(),
                    "nodes": nodes,
                    "outputs": outputs,
                }
            }
            return ArgoWorkflow(response)
        query_params = None
        if fields is not None:
            query_params = [('fields', ",".join(fields))]
        try:
            response = self.api_instance.api_client.call_api(
                '/api/v1/workflows/%s/%s' % (self.namespace, self.id),
                'GET', response_type=object, _return_http_data_only=True,
                header_params=config["http_headers"],
                query_params=query_params)
        except ApiException as e:
            if e.status == 404:
                response = self.api_instance.api_client.call_api(
                    '/api/v1/archived-workflows/%s' % self.uid,
                    'GET', response_type=object, _return_http_data_only=True,
                    header_params=config["http_headers"],
                    query_params=query_params)
            elif e.status >= 500 and e.status < 600 and retry > 0:
                logger.error("API Exception: %s" % e)
                logger.error("Remaining retry: %s" % retry)
                time.sleep(1)
                return self.query(fields=fields, retry=retry-1)
            else:
                raise e
        workflow = ArgoWorkflow(response)
        return workflow

    def query_status(
            self,
    ) -> str:
        """
        Query the status of the workflow from Argo
        The function is O(1)

        Returns:
            Pending, Running, Succeeded, Failed, Error, etc
        """
        if config["mode"] == "debug":
            wfdir = os.path.join(config["debug_workdir"], self.id)
            with open(os.path.join(wfdir, "status"), "r") as f:
                return f.read()
        workflow = self.query(fields=["status.phase"])

        if "phase" not in workflow.status:
            return "Pending"
        else:
            return workflow.status.phase

    def query_step(
            self,
            name: Union[str, List[str]] = None,
            key: Union[str, List[str]] = None,
            phase: Union[str, List[str]] = None,
            id: Union[str, List[str]] = None,
            type: Union[str, List[str]] = None,
            parent_id: Optional[str] = None,
            sort_by_generation: bool = False,
    ) -> List[ArgoStep]:
        """
        Query the existing steps of the workflow from Argo
        This function will query full steps from server [O(n)], then filter
        with conditions given in the arguments
        If you want to call this function multiple times successively,
        it is recommended to call query once and call get_step repeatedly, e.g.
        info = wf.query()
        step1 = info.get_step(key="step1")
        step2 = info.get_step(key="step2")

        Args:
            name: filter by name of step, support regex
            key: filter by key of step
            phase: filter by phase of step
            id: filter by id of step
            type: filter by type of step
            parent_id: get sub steps of a specific step
            sort_by_generation: sort results by the number of generation from
                the root node
        Returns:
            a list of steps
        """
        if config["mode"] == "debug":
            wfdir = os.path.join(config["debug_workdir"], self.id)
            if key is not None and not isinstance(key, list):
                key = [key]
            step_list = []
            for s in os.listdir(wfdir):
                stepdir = os.path.join(wfdir, s)
                if not os.path.isdir(stepdir):
                    continue
                if not os.path.exists(os.path.join(stepdir, "name")):
                    continue
                with open(os.path.join(stepdir, "name"), "r") as f:
                    _name = f.read()
                if name is not None and name != _name:
                    continue
                if key is not None and s not in key:
                    continue
                if not os.path.exists(os.path.join(stepdir, "type")):
                    continue
                with open(os.path.join(stepdir, "type"), "r") as f:
                    _type = f.read()
                if type is not None and type != _type:
                    continue
                if os.path.exists(os.path.join(stepdir, "phase")):
                    with open(os.path.join(stepdir, "phase"), "r") as f:
                        _phase = f.read()
                else:
                    _phase = "Pending"
                if phase is not None and phase != _phase:
                    continue
                children = {}
                if os.path.exists(os.path.join(stepdir, "children")):
                    with open(os.path.join(stepdir, "children"), "r") as f:
                        children = json.load(f)
                step = {
                    "workflow": self.id,
                    "displayName": _name,
                    "key": s,
                    "id": s,
                    "startedAt": os.path.getmtime(stepdir),
                    "phase": _phase,
                    "type": _type,
                    "inputs": {
                        "parameters": [],
                        "artifacts": [],
                    },
                    "outputs": {
                        "parameters": [],
                        "artifacts": [],
                    },
                    "children": children,
                }
                for io in ["inputs", "outputs"]:
                    if os.path.exists(os.path.join(stepdir, io, "parameters")):
                        for p in os.listdir(os.path.join(stepdir, io,
                                                         "parameters")):
                            if p == ".dflow":
                                continue
                            with open(os.path.join(stepdir, io, "parameters",
                                                   p), "r") as f:
                                val = f.read()
                            metadata = {"type": None}
                            if os.path.exists(os.path.join(
                                    stepdir, io, "parameters/.dflow", p)):
                                with open(os.path.join(
                                        stepdir, io, "parameters/.dflow", p),
                                        "r") as f:
                                    metadata.update(json.load(f))
                                # for backward compatible
                                if metadata["type"] not in ["str", str(str)]:
                                    val = jsonpickle.loads(val)
                            step[io]["parameters"].append({
                                "name": p, "value": val, **metadata})
                    if os.path.exists(os.path.join(stepdir, io, "artifacts")):
                        for a in os.listdir(os.path.join(stepdir, io,
                                                         "artifacts")):
                            if a == ".dflow":
                                continue
                            metadata = {}
                            if os.path.exists(os.path.join(
                                    stepdir, io, "artifacts/.dflow", a)):
                                with open(os.path.join(
                                        stepdir, io, "artifacts/.dflow", a),
                                        "r") as f:
                                    metadata = json.load(f)
                            step[io]["artifacts"].append({
                                "name": a,
                                "local_path": os.path.abspath(os.path.join(
                                    stepdir, io, "artifacts", a)),
                                **metadata,
                            })
                step = ArgoStep(step, self.id)
                step_list.append(step)
            step_list.sort(key=lambda x: x["startedAt"])
            return step_list

        return self.query().get_step(
            name=name, key=key, phase=phase, id=id, type=type,
            parent_id=parent_id, sort_by_generation=sort_by_generation)

    def query_keys_of_steps(
            self,
    ) -> List[str]:
        """
        Query the keys of existing steps of the workflow from Argo
        This function will try to get keys from the global outputs,
        which is O(1). If failed, it will downgrade to query full steps

        Returns:
            a list of keys
        """
        if config["mode"] == "debug":
            return [step.key for step in self.query_step()
                    if step.key is not None]
        outputs = self.query_global_outputs()
        if hasattr(outputs, "parameters") and any([par.startswith(
                "dflow_key_") for par in outputs.parameters]):
            return [par[10:] for par in outputs.parameters]
        else:
            logger.debug("Key-ID map not found in the global outputs, "
                         "downgrade to full query")
            return [step.key for step in self.query_step()
                    if step.key is not None]

    def query_step_by_key(
            self,
            key: Union[str, List[str]],
            name: Union[str, List[str]] = None,
            phase: Union[str, List[str]] = None,
            id: Union[str, List[str]] = None,
            type: Union[str, List[str]] = None,
    ) -> List[ArgoStep]:
        """
        Query the existing steps of the workflow from Argo by key
        This function will try to get key-ID map from the global outputs,
        then query step by ID, which is O(m) where m is the number of the
        requested keys. If failed, it will downgrade to query full steps

        Args:
            key: filter by key of step
        Returns:
            a list of steps
        """
        if isinstance(key, str):
            key = [key]

        outputs = self.query_global_outputs()
        if hasattr(outputs, "parameters") and any([par.startswith(
                "dflow_key_") for par in outputs.parameters]):
            wf_name = outputs.workflow
            key2id = {}
            for par in outputs.parameters:
                pod_name = outputs.parameters[par]["value"]
                key2id[par[10:]] = wf_name + "-" + pod_name.split("-")[-1]

            workflow = self.query(
                fields=['metadata.name'] + [
                    'status.nodes.' + key2id[k] for k in key])
            steps = workflow.get_step(name=name, phase=phase, id=id, type=type)
            return steps
        else:
            logger.debug("Key-ID map not found in the global outputs, "
                         "downgrade to full query")
            return self.query_step(key=key, name=name, phase=phase, id=id,
                                   type=type)

    def query_global_outputs(self) -> ArgoWorkflow:
        """
        Query the global outputs of the workflow from Argo
        The function is O(1)

        Args:
            key: filter by key of step
        Returns:
            a list of steps
        """
        if config["mode"] == "debug":
            wfdir = os.path.join(config["debug_workdir"], self.id)
            if not os.path.exists(os.path.join(wfdir, "outputs")):
                return None
            outputs = {"parameters": [], "artifacts": []}
            pars = os.path.join(wfdir, "outputs", "parameters")
            if os.path.exists(pars):
                for p in os.listdir(pars):
                    if p == ".dflow":
                        continue
                    with open(os.path.join(pars, p), "r") as f:
                        val = f.read()
                    _type = None
                    if os.path.exists(os.path.join(pars, ".dflow", p)):
                        with open(os.path.join(pars, ".dflow", p), "r") as f:
                            _type = json.load(f)["type"]
                        # for backward compatible
                        if _type != ["str", str(str)]:
                            val = jsonpickle.loads(val)
                    outputs["parameters"].append({
                        "name": p, "value": val, "type": _type})
            arts = os.path.join(wfdir, "outputs", "artifacts")
            if os.path.exists(arts):
                for a in os.listdir(arts):
                    if a == ".dflow":
                        continue
                    outputs["artifacts"].append({
                        "name": a,
                        "local_path": os.path.abspath(os.path.join(arts, a))})
            step = ArgoStep({"outputs": outputs}, self.id)
            return step.outputs
        workflow = self.query(fields=['metadata.name', 'status.outputs'])
        step = ArgoStep(workflow.status, workflow.metadata.name)
        if hasattr(step, "outputs"):
            step.outputs.workflow = step.workflow
            return step.outputs
        else:
            return None

    def terminate(self) -> None:
        """
        Terminate the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        if config["mode"] == "debug":
            wfdir = os.path.join(config["debug_workdir"], self.id)
            with open(os.path.join(wfdir, "pid"), "r") as f:
                pid = int(f.read())
            import psutil
            p = psutil.Process(pid)
            for c in p.children(recursive=True):
                c.terminate()
            p.terminate()
            return
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s/terminate' % (self.namespace, self.id),
            'PUT', header_params=config["http_headers"])

    def delete(self) -> None:
        """
        Delete the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s' % (self.namespace, self.id), 'DELETE',
            header_params=config["http_headers"])

    def resubmit(self) -> None:
        """
        Resubmit the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s/resubmit' % (self.namespace, self.id),
            'PUT', header_params=config["http_headers"])

    def resume(self) -> None:
        """
        Resume the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s/resume' % (self.namespace, self.id),
            'PUT', header_params=config["http_headers"])

    def retry(self) -> None:
        """
        Retry the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s/retry' % (self.namespace, self.id),
            'PUT', header_params=config["http_headers"])

    def stop(self) -> None:
        """
        Stop the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s/stop' % (self.namespace, self.id),
            'PUT', header_params=config["http_headers"])

    def suspend(self) -> None:
        """
        Suspend the workflow
        """
        if self.id is None:
            raise RuntimeError("Workflow ID is None")
        self.api_instance.api_client.call_api(
            '/api/v1/workflows/%s/%s/suspend' % (self.namespace, self.id),
            'PUT', header_params=config["http_headers"])

    def retry_steps(self, step_ids):
        assert self.query_status() == "Running"
        logger.info("Suspend workflow %s..." % self.id)
        self.suspend()
        time.sleep(5)

        logger.info("Query workflow %s..." % self.id)
        wf_info = self.query().recover()
        nodes = wf_info["status"]["nodes"]
        patch = {"status": {"nodes": {}}}
        for step_id in step_ids:
            step = ArgoStep(nodes[step_id], self.id)
            patch["status"]["nodes"][step_id] = {"phase": "Pending"}
            for node in nodes.values():
                if node["name"] != step.name and step.name.startswith(
                        node["name"]) and node["phase"] == "Failed":
                    patch["status"]["nodes"][node["id"]] = {"phase": "Running"}

            logger.info("Delete pod of step %s..." % step_id)
            step.delete_pod()

        with get_argo_api_client() as api_client:
            logger.info("Update workflow %s..." % self.id)
            api_client.call_api(
                '/api/v1/workflows/%s/%s' % (
                    config["namespace"], self.id),
                'PUT', response_type='object',
                header_params=config["http_headers"],
                body={"patch": json.dumps(patch)},
                _return_http_data_only=True)

        logger.info("Resume workflow %s..." % self.id)
        self.resume()


def get_argo_api_client(host=None, token=None):
    if host is None:
        host = config["host"]
    if token is None:
        token = config["token"]
    configuration = Configuration(host=host)
    configuration.verify_ssl = False
    if token is None:
        api_client = ApiClient(configuration)
    else:
        api_client = ApiClient(
            configuration, header_name='Authorization',
            header_value='Bearer %s' % token)
    return api_client


def query_workflows(labels: Optional[Dict[str, str]] = None,
                    fields: Optional[List[str]] = None) -> List[ArgoWorkflow]:
    if fields is None:
        fields = [
            'metadata', 'items.metadata.uid', 'items.metadata.name',
            'items.metadata.namespace', 'items.metadata.creationTimestamp',
            'items.metadata.labels', 'items.metadata.annotations',
            'items.status.phase', 'items.status.message',
            'items.status.finishedAt', 'items.status.startedAt',
            'items.status.estimatedDuration', 'items.status.progress',
            'items.spec.suspend',
        ]
    query_params = [('fields', ",".join(fields))]
    if labels is not None:
        query_params.append((
            'listOptions.labelSelector',
            ",".join(["%s=%s" % (k, v) for k, v in labels.items()])))
    with get_argo_api_client() as api_client:
        res = api_client.call_api(
            '/api/v1/workflows/%s' % config["namespace"],
            'GET', response_type='object',
            header_params=config["http_headers"],
            query_params=query_params,
            _return_http_data_only=True)
    return [ArgoWorkflow(w) for w in res["items"]] if res["items"] else []


def query_archived_workflows(
        labels: Optional[Dict[str, str]] = None,
        id: Optional[str] = None) -> List[ArgoWorkflow]:
    sel = "metadata.namespace=%s" % config["namespace"]
    if id is not None:
        sel += ",metadata.name=%s" % id
    query_params = [('listOptions.fieldSelector', sel)]
    if labels is not None:
        query_params.append((
            'listOptions.labelSelector',
            ",".join(["%s=%s" % (k, v) for k, v in labels.items()])))
    with get_argo_api_client() as api_client:
        res = api_client.call_api(
            '/api/v1/archived-workflows',
            'GET', response_type='object',
            header_params=config["http_headers"],
            query_params=query_params,
            _return_http_data_only=True)
    return [ArgoWorkflow(w) for w in res["items"]] if res["items"] else []


def parse_repo(repo_key=None, namespace=None, **kwargs):
    if repo_key is None:
        repo_key = s3_config["repo_key"]
    if namespace is None:
        namespace = config["namespace"]
    if repo_key is not None and s3_config["repo"] is None:
        with get_k8s_client(**kwargs) as k8s_client:
            core_v1_api = kubernetes.client.CoreV1Api(k8s_client)
            cm = core_v1_api.read_namespaced_config_map(
                namespace=namespace, name="artifact-repositories")
            repo = yaml.full_load(cm.data[repo_key])
            s3_config["repo"] = repo
            if "s3" in repo:
                s3_config["repo_type"] = "s3"
                s3 = repo["s3"]
            elif "oss" in repo:
                s3_config["repo_type"] = "oss"
                s3 = repo["oss"]
            if "keyFormat" in s3:
                t = "{{workflow.name}}/{{pod.name}}"
                if s3["keyFormat"].endswith(t):
                    s3_config["repo_prefix"] = s3["keyFormat"][:-len(t)]
