import contextlib
import os
import random
import shutil
import string
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

import jsonpickle

from .common import S3Artifact
from .config import config

try:
    from minio import Minio
    from minio.api import CopySource
except Exception:
    pass

s3_config = {
    "endpoint": "127.0.0.1:9000",
    "access_key": "admin",
    "secret_key": "password",
    "secure": False,
    "bucket_name": "my-bucket"
}


def download_artifact(
        artifact,
        extract: bool = True,
        **kwargs,
) -> List[str]:
    """
    Download an artifact from Argo to local

    Args:
        artifact: artifact to be downloaded
        extract: extract files if the artifact is compressed
        path: local path
        endpoint: endpoint for Minio
        access_key: access key for Minio
        secret_key: secret key for Minio
        secure: secure or not for Minio
        bucket_name: bucket name for Minio
    """
    if hasattr(artifact, "s3"):
        if hasattr(artifact, "archive") and hasattr(artifact.archive, "none")\
                and artifact.archive.none is not None:
            path = download_s3(key=artifact.s3.key, recursive=True, **kwargs)
        else:
            path = download_s3(key=artifact.s3.key, recursive=False, **kwargs)
            if path[-4:] == ".tgz" and extract:
                tf = tarfile.open(path, "r:gz")
                with tempfile.TemporaryDirectory() as tmpdir:
                    tf.extractall(tmpdir)
                    tf.close()

                    os.remove(path)
                    path = os.path.dirname(path)

                    # if the artifact contains only one directory, merge the
                    # directory with the target directory
                    ld = os.listdir(tmpdir)
                    if len(ld) == 1 and os.path.isdir(os.path.join(tmpdir,
                                                                   ld[0])):
                        merge_dir(os.path.join(tmpdir, ld[0]), path)
                    else:
                        merge_dir(tmpdir, path)

        remove_empty_dir_tag(path)
        return assemble_path_list(path, remove=True)
    else:
        raise NotImplementedError()


def upload_artifact(
        path: Union[os.PathLike, List[os.PathLike], Set[os.PathLike]],
        archive: str = "default",
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
    if not isinstance(path, (list, set)):
        path = [path]
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        path_list = []
        for i, p in enumerate(path):
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
            os.symlink(abspath, target)
            path_list.append({"dflow_list_item": relpath, "order": i})
        with open(os.path.join(tmpdir, config["catalog_file_name"] + ".%s" %
                               uuid.uuid4()), "w") as f:
            f.write(jsonpickle.dumps({"path_list": path_list}))

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

    return S3Artifact(key=key, path_list=path_list)


def copy_artifact(src, dst, sort=False) -> S3Artifact:
    """
    Copy an artifact to another on server side

    Args:
        src: source artifact
        dst: destination artifact
        sort: append the path list of dst after that of src
    """
    if hasattr(src, "s3"):
        src_key = src.s3.key
    elif hasattr(src, "key"):
        src_key = src.key
    else:
        raise NotImplementedError()

    if hasattr(dst, "s3"):
        dst_key = dst.s3.key
    elif hasattr(dst, "key"):
        dst_key = dst.key
    else:
        raise NotImplementedError()

    if sort:
        src_catalog = catalog_of_artifact(src)
        dst_catalog = catalog_of_artifact(dst)
        if src_catalog:
            if dst_catalog:
                offset = max(dst_catalog,
                            key=lambda item: item["order"])["order"] + 1
            else:
                offset = 0
            for item in src_catalog:
                item["order"] += offset
            with tempfile.TemporaryDirectory() as tmpdir:
                fname = config["catalog_file_name"] + ".%s" % uuid.uuid4()
                fpath = os.path.join(tmpdir, fname)
                with open(fpath, "w") as f:
                    f.write(jsonpickle.dumps({"path_list": src_catalog}))
                upload_s3(path=fpath, prefix=dst_key)

    copy_s3(src_key, dst_key, ignore_catalog=sort)
    return S3Artifact(key=dst_key)


def download_s3(
        key: str,
        path: os.PathLike = None,
        recursive: bool = True,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        secure: bool = None,
        bucket_name: str = None,
        **kwargs,
) -> str:
    if endpoint is None:
        endpoint = s3_config["endpoint"]
    if access_key is None:
        access_key = s3_config["access_key"]
    if secret_key is None:
        secret_key = s3_config["secret_key"]
    if secure is None:
        secure = s3_config["secure"]
    if bucket_name is None:
        bucket_name = s3_config["bucket_name"]
    if path is None:
        path = "."
    client = Minio(endpoint=endpoint, access_key=access_key,
                   secret_key=secret_key, secure=secure)
    if recursive:
        for obj in client.list_objects(bucket_name=bucket_name, prefix=key,
                                       recursive=True):
            rel_path = obj.object_name[len(key):]
            if rel_path[:1] == "/":
                rel_path = rel_path[1:]
            if rel_path == "":
                file_path = os.path.join(path, os.path.basename(key))
            else:
                file_path = os.path.join(path, rel_path)
            client.fget_object(bucket_name=bucket_name,
                               object_name=obj.object_name,
                               file_path=file_path)
    else:
        path = os.path.join(path, os.path.basename(key))
        client.fget_object(bucket_name=bucket_name,
                           object_name=key, file_path=path)
    return path


def upload_s3(
        path: os.PathLike,
        key: str = None,
        prefix: str = None,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        secure: bool = None,
        bucket_name: str = None,
        **kwargs,
) -> str:
    if endpoint is None:
        endpoint = s3_config["endpoint"]
    if access_key is None:
        access_key = s3_config["access_key"]
    if secret_key is None:
        secret_key = s3_config["secret_key"]
    if secure is None:
        secure = s3_config["secure"]
    if bucket_name is None:
        bucket_name = s3_config["bucket_name"]
    client = Minio(endpoint=endpoint, access_key=access_key,
                   secret_key=secret_key, secure=secure)
    if key is not None:
        pass
    elif prefix is not None:
        if prefix[-1] != "/":
            prefix += "/"
        objs = list(client.list_objects(
            bucket_name=bucket_name, prefix=prefix))
        if len(objs) == 1 and objs[0].object_name[-1] == "/":
            prefix = objs[0].object_name
        key = "%s%s" % (prefix, os.path.basename(path))
    else:
        key = "upload/%s/%s" % (uuid.uuid4(), os.path.basename(path))
    if os.path.isfile(path):
        client.fput_object(bucket_name=bucket_name,
                           object_name=key, file_path=path)
    elif os.path.isdir(path):
        for dn, ds, fs in os.walk(path, followlinks=True):
            rel_path = dn[len(path):]
            if rel_path == "":
                pass
            elif rel_path[0] != "/":
                rel_path = "/" + rel_path
            for f in fs:
                client.fput_object(bucket_name=bucket_name,
                                   object_name="%s%s/%s" %
                                   (key, rel_path, f),
                                   file_path=os.path.join(dn, f))
    return key


def copy_s3(
        src_key: str,
        dst_key: str,
        recursive: bool = True,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        secure: bool = None,
        bucket_name: str = None,
        ignore_catalog: bool = False,
        **kwargs,
) -> None:
    if endpoint is None:
        endpoint = s3_config["endpoint"]
    if access_key is None:
        access_key = s3_config["access_key"]
    if secret_key is None:
        secret_key = s3_config["secret_key"]
    if secure is None:
        secure = s3_config["secure"]
    if bucket_name is None:
        bucket_name = s3_config["bucket_name"]
    client = Minio(endpoint=endpoint, access_key=access_key,
                   secret_key=secret_key, secure=secure)
    if recursive:
        if src_key[-1] != "/":
            src_key += "/"
        src_objs = list(client.list_objects(
            bucket_name=bucket_name, prefix=src_key))
        if len(src_objs) == 1 and src_objs[0].object_name[-1] == "/":
            src_key = src_objs[0].object_name
        if dst_key[-1] != "/":
            dst_key += "/"
        dst_objs = list(client.list_objects(
            bucket_name=bucket_name, prefix=dst_key))
        if len(dst_objs) == 1 and dst_objs[0].object_name[-1] == "/":
            dst_key = dst_objs[0].object_name
        for obj in client.list_objects(bucket_name=bucket_name,
                                       prefix=src_key, recursive=True):
            if ignore_catalog:
                fname = os.path.basename(obj.object_name)
                if fname[:len(config["catalog_file_name"])] \
                        == config["catalog_file_name"]:
                    continue
            client.copy_object(bucket_name, dst_key + obj.object_name[len(
                src_key):], CopySource(bucket_name, obj.object_name))
    else:
        client.copy_object(bucket_name, dst_key,
                           CopySource(bucket_name, src_key))


def catalog_of_artifact(art, **kwargs) -> List[dict]:
    if hasattr(art, "s3"):
        key = art.s3.key
    elif hasattr(art, "key"):
        key = art.key
    else:
        return []

    endpoint = kwargs["endpoint"] if "endpoint" in kwargs \
        else s3_config["endpoint"]
    access_key = kwargs["access_key"] if "access_key" in kwargs \
        else s3_config["access_key"]
    secret_key = kwargs["secret_key"] if "secret_key" in kwargs \
        else s3_config["secret_key"]
    secure = kwargs["secure"] if "secure" in kwargs else s3_config["secure"]
    bucket_name = kwargs["bucket_name"] if "bucket_name" in kwargs \
        else s3_config["bucket_name"]

    client = Minio(endpoint=endpoint, access_key=access_key,
                   secret_key=secret_key, secure=secure)
    catalog = []
    with tempfile.TemporaryDirectory() as tmpdir:
        objs = list(client.list_objects(bucket_name=bucket_name, prefix=key))
        if len(objs) == 1 and objs[0].object_name[-1] == "/":
            key = objs[0].object_name
        for obj in client.list_objects(bucket_name=bucket_name, prefix=key):
            fname = obj.object_name[len(key):]
            if fname[:len(config["catalog_file_name"])] == \
                    config["catalog_file_name"]:
                client.fget_object(
                    bucket_name=bucket_name, object_name=obj.object_name,
                    file_path=os.path.join(tmpdir, fname))
                with open(os.path.join(tmpdir, fname), "r") as f:
                    catalog += jsonpickle.loads(f.read())['path_list']
    return catalog


def path_list_of_artifact(art, **kwargs) -> List[str]:
    return convert_dflow_list(catalog_of_artifact(art, **kwargs))


def merge_dir(src, dst):
    for f in os.listdir(src):
        src_file = os.path.join(src, f)
        dst_file = os.path.join(dst, f)
        if not os.path.exists(dst_file):
            shutil.move(src_file, dst_file)
        elif os.path.isdir(dst_file):
            if os.path.isdir(src_file):
                merge_dir(src_file, dst_file)
            else:
                shutil.rmtree(dst_file)
                shutil.move(src_file, dst_file)
        else:
            os.remove(dst_file)
            shutil.move(src_file, dst_file)


def copy_file(src, dst, func=os.link):
    os.makedirs(os.path.abspath(os.path.dirname(dst)), exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, dst, copy_function=func)
    elif os.path.isfile(src):
        func(src, dst)
    else:
        raise RuntimeError("File %s not found" % src)


def assemble_path_list(art_path, remove=False):
    path_list = []
    if os.path.isdir(art_path):
        dflow_list = []
        for f in os.listdir(art_path):
            if f[:len(config["catalog_file_name"])] == \
                    config["catalog_file_name"]:
                with open('%s/%s' % (art_path, f), 'r') as fd:
                    for item in jsonpickle.loads(fd.read())['path_list']:
                        if item not in dflow_list:
                            dflow_list.append(item)  # remove duplicate
                if remove:
                    os.remove(os.path.join(art_path, f))
        if len(dflow_list) > 0:
            path_list = list(map(lambda x: os.path.join(
                art_path, x) if x is not None else None,
                convert_dflow_list(dflow_list)))
    return path_list


def convert_dflow_list(dflow_list):
    dflow_list.sort(key=lambda x: x['order'])
    return list(map(lambda x: x['dflow_list_item'], dflow_list))


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

    sub = subprocess.Popen(
        args=cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs
    )
    if input is not None:
        sub.stdin.write(bytes(input, encoding=sys.stdin.encoding))
    out, err = sub.communicate()
    return_code = sub.poll()
    out = out.decode(sys.stdin.encoding)
    err = err.decode(sys.stdin.encoding)
    if raise_error:
        assert return_code == 0, f"Command {cmd} failed: \n{err}"
    return return_code, out, err
