import os
import uuid
import shutil
from pathlib import Path

import pytest
from dflow import copy_artifact, upload_artifact, S3Artifact
from dflow.utils import catalog_of_artifact, run_command, set_directory


def test_set_directory():
    pwd = Path.cwd()
    with set_directory("test_dir", mkdir=True) as wdir:
        assert str(wdir) == str(pwd / "test_dir")
        assert os.getcwd() == str(wdir)
    shutil.rmtree(wdir)


def test_run_command():
    code, out, err = run_command("echo test")
    assert code == 0
    assert out == "test\n"


def test_run_command_err():
    with pytest.raises(AssertionError):
        run_command(["python", "-c", "raise ValueError('error')"])


def test_run_command_input():
    code, out, err = run_command(["sh"], input="echo test\nexit")
    assert code == 0
    assert out == "test\n"


def test_copy_artifact():
    with open("foo.txt", "w"):
        pass
    with open("bar.txt", "w"):
        pass
    art_1 = upload_artifact(["foo.txt"], archive=None)
    art_2 = upload_artifact(["bar.txt"], archive=None)
    copy_artifact(art_1, art_2, sort=True)
    catalog = catalog_of_artifact(art_2)
    catalog.sort(key=lambda x: x["order"])
    assert catalog == [{'dflow_list_item': 'bar.txt', 'order': 0},
                       {'dflow_list_item': 'foo.txt', 'order': 1}]

    art_1 = upload_artifact(["foo.txt"], archive=None)
    art_2 = upload_artifact(["bar.txt"], archive=None)
    copy_artifact(art_2, art_1, sort=True)
    catalog = catalog_of_artifact(art_1)
    catalog.sort(key=lambda x: x["order"])
    assert catalog == [{'dflow_list_item': 'foo.txt', 'order': 0},
                       {'dflow_list_item': 'bar.txt', 'order': 1}]

    os.remove("foo.txt")
    os.remove("bar.txt")


def test_copy_artifact_dst_none():
    with open("foo_1.txt", "w"):
        pass
    art_1 = S3Artifact(key=f"test-{uuid.uuid4()}")
    art_2 = upload_artifact(["foo_1.txt"], archive=None)
    copy_artifact(art_2, art_1, sort=True)
    catalog = catalog_of_artifact(art_1)
    catalog.sort(key=lambda x: x["order"])
    assert catalog == [{'dflow_list_item': 'foo_1.txt', 'order': 0}]

    os.remove("foo_1.txt")