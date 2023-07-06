import abc
import contextlib
import hashlib
import inspect
import logging
import os
import pkgutil
import random
import selectors
import shlex
import shutil
import string
import subprocess
import sys
import tarfile
import tempfile
import uuid
from abc import ABC
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import jsonpickle

from .common import LocalArtifact, S3Artifact
from .config import config, s3_config

try:
    from minio import Minio
    from minio.api import CopySource
except Exception:
    pass


def get_key(artifact, raise_error=True):
    if hasattr(artifact, "s3") and hasattr(artifact.s3, "key"):
        return artifact.s3.key
    elif hasattr(artifact, "oss") and hasattr(artifact.oss, "key"):
        key = artifact.oss.key
        if key.startswith(s3_config["repo_prefix"]):
            return key[len(s3_config["repo_prefix"]):]
        else:
            return key
    elif hasattr(artifact, "key"):
        return artifact.key
    else:
        if raise_error:
            raise FileNotFoundError(
                "The artifact does not exist in the storage.")
        else:
            return None


def set_key(artifact, key):
    if hasattr(artifact, "s3") and hasattr(artifact.s3, "key"):
        artifact.s3.key = key
    elif hasattr(artifact, "oss") and hasattr(artifact.oss, "key"):
        if not key.startswith(s3_config["repo_prefix"]):
            key = s3_config["repo_prefix"] + key
        artifact.oss.key = key
    elif hasattr(artifact, "key"):
        artifact.key = key


def download_artifact(
        artifact,
        extract: bool = True,
        sub_path: Optional[str] = None,
        slice: Optional[int] = None,
        path: os.PathLike = ".",
        debug_download: bool = False,
        remove_catalog: bool = True,
        **kwargs,
) -> List[str]:
    """
    Download an artifact from Argo to local

    Args:
        artifact: artifact to be downloaded
        extract: extract files if the artifact is compressed
        sub_path: download a subdir of an artifact
        slice: download a slice of an artifact
        path: local path
        endpoint: endpoint for Minio
        access_key: access key for Minio
        secret_key: secret key for Minio
        secure: secure or not for Minio
        bucket_name: bucket name for Minio
        skip_exists: skip files with the same MD5
    """
    if config["mode"] == "debug" and not debug_download:
        linktree(artifact.local_path, path)
        return assemble_path_list(path, remove=remove_catalog)

    key = get_key(artifact)

    if slice is not None:
        sub_path = path_list_of_artifact(artifact)[slice]

    if sub_path is not None:
        key = key + "/" + sub_path
        path = os.path.join(path, os.path.dirname(sub_path))
        download_s3(key=key, recursive=True, path=path, keep_dir=True,
                    **kwargs)
        path = os.path.join(path, os.path.basename(sub_path))
        if config["detect_empty_dir"]:
            remove_empty_dir_tag(path)
        return path

    path = download_s3(key=key, recursive=True, path=path, **kwargs)
    if key[-4:] == ".tgz" and extract:
        path = os.path.join(path, os.path.basename(key))
        tf = tarfile.open(path, "r:gz")
        with tempfile.TemporaryDirectory() as tmpdir:
            tf.extractall(tmpdir)
            tf.close()

            os.remove(path)
            path = os.path.dirname(path)

            # if the artifact contains only one directory, merge the
            # directory with the target directory
            ld = os.listdir(tmpdir)
            if len(ld) == 1 and os.path.isdir(os.path.join(tmpdir, ld[0])):
                merge_dir(os.path.join(tmpdir, ld[0]), path)
            else:
                merge_dir(tmpdir, path)

    if config["detect_empty_dir"]:
        remove_empty_dir_tag(path)
    return assemble_path_list(path, remove=remove_catalog)


def flatten(d: Union[list, dict]) -> dict:
    def handle(obj, prefix):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = prefix + "." + k if prefix else k
                if isinstance(v, (list, dict)):
                    handle(v, key)
                else:
                    flat[key] = v
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                key = prefix + "." + str(i) if prefix else str(i)
                if isinstance(v, (list, dict)):
                    handle(v, key)
                else:
                    flat[key] = v
    flat = {}
    handle(d, "")
    return flat


def dict2list(d: dict):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = dict2list(v)
    try:
        lst = []
        for k, v in d.items():
            i = int(k)
            if i < len(lst):
                lst[i] = v
            else:
                lst += [None] * (i - len(lst)) + [v]
        return lst
    except Exception:
        return d


def expand(d: dict) -> Union[list, dict]:
    exp = {}
    for k, v in d.items():
        fields = str(k).split(".")
        tmp = exp
        for field in fields[:-1]:
            if field not in tmp:
                tmp[field] = {}
            tmp = tmp[field]
        field = fields[-1]
        tmp[field] = v
    exp = dict2list(exp)
    return exp


def upload_artifact(
        path: Union[os.PathLike, List[os.PathLike], Set[os.PathLike],
                    Dict[str, os.PathLike], list, dict],
        archive: str = "default",
        namespace: Optional[str] = None,
        dataset_name: Optional[str] = None,
        **kwargs,
) -> S3Artifact:
    """
    Upload an artifact from local to Argo

    Args:
        path: local path
        archive: compress format of the artifact, None for no compression
        endpoint: endpoint for Minio
        access_key: access key for Minio
        secret_key: secret key for Minio
        secure: secure or not for Minio
        bucket_name: bucket name for Minio
    """
    if archive == "default":
        archive = config["archive_mode"]
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        if isinstance(path, dict):
            pairs = flatten(path).items()
        elif isinstance(path, (list, set)):
            pairs = enumerate(path)
        else:
            pairs = [(0, path)]
        path_list = []
        for i, p in pairs:
            logging.debug("upload artifact: handle path: %s" % p)
            if p is None:
                continue
            if not os.path.exists(p):
                raise RuntimeError("File or directory %s not found" % p)
            abspath = os.path.abspath(p)
            # subpath of current dir
            if abspath.find(cwd + "/") == 0 or abspath.find(cwd + "\\") == 0:
                relpath = abspath[len(cwd)+1:]
            else:
                if abspath[0] == "/":
                    relpath = abspath[1:]
                else:
                    # For Windows
                    relpath = abspath[abspath.find(":")+2:]
            target = os.path.join(tmpdir, relpath)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if config["mode"] == "debug" and cwd.startswith(p):
                # To avoid recursive symlink
                try:
                    copy_file(abspath, target, link)
                except Exception:
                    copy_file(abspath, target, shutil.copy)
            else:
                os.symlink(abspath, target)
            path_list.append({"dflow_list_item": relpath.replace("\\", "/"),
                              "order": i})

        catalog_dir = os.path.join(tmpdir, config["catalog_dir_name"])
        os.makedirs(catalog_dir, exist_ok=True)
        with open(os.path.join(catalog_dir, str(uuid.uuid4())), "w") as f:
            f.write(jsonpickle.dumps({"path_list": path_list}))

        if config["mode"] == "debug":
            os.makedirs("upload", exist_ok=True)
            resdir = shutil.move(tmpdir, "upload")
            # To prevent exception in destruction
            os.makedirs(tmpdir, exist_ok=True)
            return LocalArtifact(local_path=os.path.abspath(resdir))

        if archive == "tar":
            os.chdir(os.path.dirname(tmpdir))
            tf = tarfile.open(os.path.basename(tmpdir) +
                              ".tgz", "w:gz", dereference=True)
            tf.add(os.path.basename(tmpdir))
            tf.close()
            os.chdir(cwd)
            key = upload_s3(path=tmpdir + ".tgz", **kwargs)
            os.remove(tmpdir + ".tgz")
        else:
            key = upload_s3(path=tmpdir, **kwargs)

    logging.debug("upload artifact: finished")

    urn = ""
    if namespace is not None and dataset_name is not None:
        if config["lineage"]:
            urn = config["lineage"].register_artifact(
                namespace, dataset_name, key, **kwargs)
        else:
            logging.warn("Lineage client not provided")

    return S3Artifact(key=key, path_list=path_list, urn=urn)


def copy_artifact(src, dst, sort=False) -> S3Artifact:
    """
    Copy an artifact to another on server side

    Args:
        src: source artifact
        dst: destination artifact
        sort: append the path list of dst after that of src
    """
    src_key = get_key(src)
    dst_key = get_key(dst)

    ignore_catalog = False
    if sort:
        src_catalog = catalog_of_artifact(src)
        dst_catalog = catalog_of_artifact(dst)
        if src_catalog and dst_catalog:
            offset = max(dst_catalog,
                         key=lambda item: item["order"])["order"] + 1
            for item in src_catalog:
                item["order"] += offset
            with tempfile.TemporaryDirectory() as tmpdir:
                catalog_dir = os.path.join(tmpdir, config["catalog_dir_name"])
                os.makedirs(catalog_dir, exist_ok=True)
                fpath = os.path.join(catalog_dir, str(uuid.uuid4()))
                with open(fpath, "w") as f:
                    f.write(jsonpickle.dumps({"path_list": src_catalog}))
                upload_s3(path=catalog_dir, prefix=dst_key)
                ignore_catalog = True

    copy_s3(src_key, dst_key, ignore_catalog=ignore_catalog)
    return S3Artifact(key=dst_key)


def get_md5(f):
    md5 = hashlib.md5()
    with open(f, "rb") as fd:
        for chunk in iter(lambda: fd.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def download_s3(
        key: str,
        path: os.PathLike = ".",
        recursive: bool = True,
        skip_exists: bool = False,
        keep_dir: bool = False,
        **kwargs,
) -> str:
    if s3_config["storage_client"] is not None:
        client = s3_config["storage_client"]
    else:
        client = MinioClient(**kwargs)
    if recursive:
        from tqdm import tqdm
        for obj in tqdm(client.list(prefix=key, recursive=True)):
            rel_path = obj[len(key):]
            if rel_path[:1] == "/":
                rel_path = rel_path[1:]
            if rel_path == "":
                file_path = os.path.join(path, os.path.basename(key))
            elif keep_dir:
                file_path = os.path.join(path, os.path.basename(key), rel_path)
            else:
                file_path = os.path.join(path, rel_path)

            if skip_exists and os.path.isfile(file_path):
                remote_md5 = client.get_md5(key=obj)
                local_md5 = get_md5(file_path)
                if remote_md5 == local_md5:
                    logging.debug("skip object: %s" % obj)
                    continue

            client.download(key=obj, path=file_path)
    else:
        path = os.path.join(path, os.path.basename(key))
        client.download(key=key, path=path)
    return path


def upload_s3(
        path: os.PathLike,
        key: Optional[str] = None,
        prefix: Optional[str] = None,
        **kwargs,
) -> str:
    if s3_config["storage_client"] is not None:
        client = s3_config["storage_client"]
    else:
        client = MinioClient(**kwargs)
    if key is not None:
        pass
    elif prefix is not None:
        if prefix[-1] != "/":
            prefix += "/"
        objs = client.list(prefix=prefix)
        if len(objs) == 1 and objs[0][-1] == "/":
            prefix = objs[0]
        key = "%s%s" % (prefix, os.path.basename(path))
    else:
        key = "%supload/%s/%s" % (s3_config["prefix"],
                                  uuid.uuid4(), os.path.basename(path))
    if os.path.isfile(path):
        client.upload(key=key, path=path)
    elif os.path.isdir(path):
        for dn, ds, fs in os.walk(path, followlinks=True):
            rel_path = dn[len(path):]
            if rel_path == "":
                pass
            elif rel_path[0] != "/":
                rel_path = "/" + rel_path
            for f in fs:
                client.upload(key="%s%s/%s" % (key, rel_path, f),
                              path=os.path.join(dn, f))
    return key


def copy_s3(
        src_key: str,
        dst_key: str,
        recursive: bool = True,
        ignore_catalog: bool = False,
        **kwargs,
) -> None:
    if s3_config["storage_client"] is not None:
        client = s3_config["storage_client"]
    else:
        client = MinioClient(**kwargs)
    if recursive:
        if src_key[-1] != "/":
            src_key += "/"
        src_objs = client.list(prefix=src_key)
        if len(src_objs) == 1 and src_objs[0][-1] == "/":
            src_key = src_objs[0]
        if dst_key[-1] != "/":
            dst_key += "/"
        dst_objs = client.list(prefix=dst_key)
        if len(dst_objs) == 1 and dst_objs[0][-1] == "/":
            dst_key = dst_objs[0]
        for obj in client.list(prefix=src_key, recursive=True):
            if ignore_catalog:
                fields = obj.split("/")
                if len(fields) > 1 and fields[-2] == \
                        config["catalog_dir_name"]:
                    continue
            client.copy(obj, dst_key + obj[len(src_key):])
    else:
        client.copy(src_key, dst_key)


def catalog_of_artifact(art, **kwargs) -> List[dict]:
    key = get_key(art, raise_error=False)
    if not key:
        return []
    if key[-1] != "/":
        key += "/"

    if s3_config["storage_client"] is not None:
        client = s3_config["storage_client"]
    else:
        client = MinioClient(**kwargs)
    catalog = []
    with tempfile.TemporaryDirectory() as tmpdir:
        objs = client.list(prefix=key)
        if len(objs) == 1 and objs[0][-1] == "/":
            key = objs[0]
        prefix = key + config["catalog_dir_name"] + "/"
        for obj in client.list(prefix=prefix):
            fname = obj[len(prefix):]
            client.download(key=obj, path=os.path.join(tmpdir, fname))
            with open(os.path.join(tmpdir, fname), "r") as f:
                catalog += jsonpickle.loads(f.read())['path_list']
    return catalog


def path_list_of_artifact(art, **kwargs) -> List[str]:
    return convert_dflow_list(catalog_of_artifact(art, **kwargs))


def force_move(src, dst):
    if os.path.exists(dst):
        if os.path.samefile(src, dst):
            return
        os.remove(dst)
    shutil.move(src, dst)


def merge_dir(src, dst, func=force_move):
    for f in os.listdir(src):
        src_file = os.path.join(src, f)
        dst_file = os.path.join(dst, f)
        if os.path.isdir(src_file):
            if os.path.isfile(dst_file):
                os.remove(dst_file)
            os.makedirs(dst_file, exist_ok=True)
            merge_dir(src_file, dst_file, func)
        elif os.path.isfile(src_file):
            if os.path.isdir(dst_file):
                shutil.rmtree(dst_file)
            func(src_file, dst_file)


def link(src, dst):
    # follow_symlinks=True of os.link not work on Linux
    if os.path.islink(src):
        os.link(os.path.realpath(src), dst)
    else:
        os.link(src, dst)


def copy_file(src, dst, func=link):
    os.makedirs(os.path.abspath(os.path.dirname(dst)), exist_ok=True)
    if os.path.isdir(src):
        try:
            shutil.copytree(src, dst, copy_function=func)
        except FileExistsError:
            pass
    elif os.path.isfile(src):
        func(src, dst)
    else:
        raise RuntimeError("File %s not found" % src)


def assemble_path_list(art_path, remove=False):
    path_list = []
    if os.path.isdir(art_path):
        dflow_list = []
        catalog_dir = os.path.join(art_path, config["catalog_dir_name"])
        if os.path.exists(catalog_dir):
            for f in os.listdir(catalog_dir):
                with open(os.path.join(catalog_dir, f), 'r') as fd:
                    for item in jsonpickle.loads(fd.read())['path_list']:
                        if item not in dflow_list:
                            dflow_list.append(item)  # remove duplicate
            if remove:
                shutil.rmtree(catalog_dir)
        if len(dflow_list) > 0:
            path_list = list(map(lambda x: os.path.join(
                art_path, x) if x is not None else None,
                convert_dflow_list(dflow_list)))
    return path_list


def convert_dflow_list(dflow_list):
    dflow_list.sort(key=lambda x: x['order'])
    return list(map(lambda x: x['dflow_list_item'], dflow_list))


def assemble_path_dict(art_path, remove=False):
    path_dict = {}
    if os.path.isdir(art_path):
        dflow_list = []
        catalog_dir = os.path.join(art_path, config["catalog_dir_name"])
        if os.path.exists(catalog_dir):
            for f in os.listdir(catalog_dir):
                with open(os.path.join(catalog_dir, f), 'r') as fd:
                    for item in jsonpickle.loads(fd.read())['path_list']:
                        if item not in dflow_list:
                            dflow_list.append(item)  # remove duplicate
            if remove:
                shutil.rmtree(catalog_dir)
        if len(dflow_list) > 0:
            for item in dflow_list:
                if item["dflow_list_item"] is None:
                    path_dict[item["order"]] = None
                else:
                    path_dict[item["order"]] = os.path.join(
                        art_path, item["dflow_list_item"])
    return path_dict


def assemble_path_nested_dict(art_path, remove=False):
    return expand(assemble_path_dict(art_path, remove))


def remove_empty_dir_tag(path):
    for dn, ds, fs in os.walk(path, followlinks=True):
        if ".empty_dir" in fs:
            os.remove(os.path.join(dn, ".empty_dir"))


def randstr(length: int = 5) -> str:
    return "".join(random.sample(string.digits + string.ascii_lowercase,
                                 length))


@contextlib.contextmanager
def set_directory(dirname: os.PathLike, mkdir: bool = False):
    """
    Set current workding directory within context

    Parameters
    ----------
    dirname : os.PathLike
        The directory path to change to
    mkdir: bool
        Whether make directory if `dirname` does not exist

    Yields
    ------
    path: Path
        The absolute path of the changed working directory

    Examples
    --------
    >>> with set_directory("some_path"):
    ...    do_something()
    """
    pwd = os.getcwd()
    path = Path(dirname).resolve()
    if mkdir:
        path.mkdir(exist_ok=True, parents=True)
    os.chdir(path)
    yield path
    os.chdir(pwd)


def run_command(
    cmd: Union[List[str], str],
    raise_error: bool = True,
    input: Optional[str] = None,
    try_bash: bool = False,
    interactive: bool = True,
    print_oe: bool = False,
    **kwargs,
) -> Tuple[int, str, str]:
    """
    Run shell command in subprocess

    Parameters:
    ----------
    cmd: list of str, or str
        Command to execute
    raise_error: bool
        Wheter to raise an error if the command failed
    input: str, optional
        Input string for the command
    try_bash: bool
        Try to use bash if bash exists, otherwise use sh
    **kwargs:
        Arguments in subprocess.Popen

    Raises:
    ------
    AssertionError:
        Raises if the error failed to execute and `raise_error` set to `True`

    Return:
    ------
    return_code: int
        The return code of the command
    out: str
        stdout content of the executed command
    err: str
        stderr content of the executed command
    """
    if isinstance(cmd, str):
        cmd = cmd.split()
    elif isinstance(cmd, list):
        cmd = [str(x) for x in cmd]

    if try_bash:
        arg = "-ic" if interactive else "-c"
        script = "if command -v bash 2>&1 >/dev/null; then bash %s " % arg + \
            shlex.quote(" ".join(cmd)) + "; else " + " ".join(cmd) + "; fi"
        cmd = [script]
        kwargs["shell"] = True

    with subprocess.Popen(
        args=cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    ) as sub:
        if input is not None:
            sub.stdin.write(bytes(input, encoding=sys.stdout.encoding))
            sub.stdin.close()
        if print_oe:
            out = ""
            err = ""
            sel = selectors.DefaultSelector()
            sel.register(sub.stdout, selectors.EVENT_READ)
            sel.register(sub.stderr, selectors.EVENT_READ)
            ok = True
            while ok:
                for key, _ in sel.select():
                    line = key.fileobj.readline().decode(sys.stdout.encoding)
                    if not line:
                        ok = False
                        break
                    if key.fileobj is sub.stdout:
                        sys.stdout.write(line)
                        out += line
                    else:
                        sys.stderr.write(line)
                        err += line
            sub.wait()
        else:
            out, err = sub.communicate()
            out = out.decode(sys.stdout.encoding)
            err = err.decode(sys.stdout.encoding)
        return_code = sub.poll()
    if raise_error:
        assert return_code == 0, "Command %s failed: \n%s" % (cmd, err)
    return return_code, out, err


def subclass_or_none(m, cls):
    if inspect.isclass(m) and issubclass(m, cls) and m != cls:
        return m
    elif isinstance(m, cls) and m.__class__ != cls:
        return m.__class__
    else:
        return None


def find_subclass(pkg, cls):
    subclasses = []
    for _, m in inspect.getmembers(pkg):
        s = subclass_or_none(m, cls)
        if s is not None and s not in subclasses:
            subclasses.append(m)
    if hasattr(pkg, "__path__"):
        for path in pkg.__path__:
            for dir, _, _ in os.walk(path):
                subpkg = (pkg.__name__ + dir[len(path):]).replace("/", ".")
                for _, name, _ in pkgutil.iter_modules([dir]):
                    try:
                        mod = __import__(subpkg + "." + name, fromlist=subpkg)
                        for _, m in inspect.getmembers(mod):
                            s = subclass_or_none(m, cls)
                            if s is not None and s not in subclasses:
                                subclasses.append(s)
                    except Exception as e:
                        logging.warning("Fail to inspect submodule %s: %s" % (
                            name, e))
    return subclasses


def linktree(src, dst, func=os.symlink):
    merge_dir(src, dst, partial(force_link, func=func))


def force_link(src, dst, func=os.symlink):
    if os.path.exists(dst):
        if os.path.samefile(src, dst):
            return
        os.remove(dst)
    func(src, dst)


class StorageClient(ABC):
    @abc.abstractmethod
    def upload(self, key: str, path: str) -> None:
        pass

    @abc.abstractmethod
    def download(self, key: str, path: str) -> None:
        pass

    @abc.abstractmethod
    def list(self, prefix: str, recursive: bool = False) -> List[str]:
        pass

    @abc.abstractmethod
    def copy(self, src: str, dst: str) -> None:
        pass

    @abc.abstractmethod
    def get_md5(self, key: str) -> str:
        pass


class MinioClient(StorageClient):
    def __init__(self,
                 endpoint: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 secure: Optional[bool] = None,
                 bucket_name: Optional[str] = None,
                 **kwargs,
                 ) -> None:
        self.client = Minio(
            endpoint=endpoint if endpoint is not None else
            s3_config["endpoint"],
            access_key=access_key if access_key is not None else
            s3_config["access_key"],
            secret_key=secret_key if secret_key is not None else
            s3_config["secret_key"],
            secure=secure if secure is not None else s3_config["secure"],
        )
        self.bucket_name = bucket_name if bucket_name is not None else \
            s3_config["bucket_name"]

    def upload(self, key: str, path: str) -> None:
        self.client.fput_object(bucket_name=self.bucket_name,
                                object_name=key, file_path=path)

    def download(self, key: str, path: str) -> None:
        self.client.fget_object(bucket_name=self.bucket_name,
                                object_name=key, file_path=path)

    def list(self, prefix: str, recursive: bool = False) -> List[str]:
        return [obj.object_name for obj in self.client.list_objects(
            bucket_name=self.bucket_name, prefix=prefix, recursive=recursive)]

    def copy(self, src: str, dst: str) -> None:
        self.client.copy_object(self.bucket_name, dst,
                                CopySource(self.bucket_name, src))

    def get_md5(self, key: str) -> str:
        return self.client.stat_object(bucket_name=self.bucket_name,
                                       object_name=key).etag
