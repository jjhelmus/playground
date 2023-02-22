#! /usr/bin/env python
"""
Create a conda child environement

A child environment is based on a parent environment and appear to contain
all of the their packages. Additional packages can be installed into the
child environement using conda or pip without effecting the parent 
environment. Packages from the parent environment cannot be removed or
changed in the child environment
"""

import argparse
import os
from os.path import isdir

from conda._vendor.boltons.setutils import IndexedSet
from conda.api import PrefixData
from conda.base.context import locate_prefix_by_name
from conda.cli.common import confirm_yn
from conda.cli.install import check_prefix, handle_txn
from conda.common.compat import encode_environment
from conda.core.link import PrefixSetup, UnlinkLinkTransaction
from conda.exceptions import EnvironmentLocationNotFound
from conda.gateways.disk.create import write_as_json_to_file
from conda.gateways.disk.delete import rm_rf
from conda.gateways.disk.test import is_conda_environment
from conda.gateways.subprocess import subprocess_call
from conda.utils import wrap_subprocess_call


def link_parent_python_to_child(parent_prefix: str, child_prefix: str) -> None:
    """Link the parent and child python environments."""
    # create run script
    executable_call = [
        "python",
        "-m",
        "venv",
        "--without-pip",
        "--system-site-packages",
        child_prefix,
    ]
    script, command = wrap_subprocess_call(
        os.environ["CONDA_ROOT"],
        parent_prefix,
        False,
        False,
        executable_call,
        use_system_tmp_path=True,
    )

    # run script
    response = subprocess_call(
        command,
        env=encode_environment(os.environ.copy()),
        path=os.getcwd(),
        raise_on_error=False,
        capture_output=False,
    )

    # cleanup
    rm_rf(script)
    if response.rc != 0:
        raise ValueError


def copy_conda_meta(parent_prefix: str, child_prefix: str) -> None:
    """Copy a modified version of conda-meta from the parent to child"""
    parent_prefixdata = PrefixData(parent_prefix)
    for prefix_record in parent_prefixdata.iter_records():
        prefix_record.files = ()
        prefix_record.paths_data = None
        prefix_record.package_type = "virtual_system"
        filename = prefix_record.fn
        json_fn = filename.replace(".conda", ".json").replace(".tar.bz2", ".json")
        prefix_record_json_path = os.path.join(child_prefix, "conda-meta", json_fn)
        write_as_json_to_file(prefix_record_json_path, prefix_record)
    # TODO this transaction should be represented in child_prefix/conda-meta/history


def create_empty_child_enviroment(child_prefix: str, args) -> None:
    """Create an empty child conda environment."""
    if is_conda_environment(child_prefix):
        confirm_yn(
            f"WARNING: A conda environment already exists at '{child_prefix}'\n"
            "Remove existing environment",
            default="no",
            dry_run=False,
        )
        rm_rf(child_prefix)
    elif isdir(child_prefix):
        confirm_yn(
            f"WARNING: A directory already exists at the target location '{child_prefix}'\n"
            "but it is not a conda environment.\n"
            "Continue creating environment",
            default="no",
            dry_run=False,
        )
    check_prefix(child_prefix)
    # create the empty child environment
    unlink_link_transaction = UnlinkLinkTransaction(
        PrefixSetup(
            child_prefix,
            IndexedSet([]),
            IndexedSet([]),
            frozenset(),
            frozenset(),
            frozenset(),
        )
    )
    # TODO this generated a y/n confirmation that should be skipped
    handle_txn(unlink_link_transaction, child_prefix, args, True)


def main() -> int:
    """conda-child cli entry point"""
    parser = argparse.ArgumentParser(description="Create a child conda enviroment")

    parent_environment_group = parser.add_argument_group(
        "Parent Environment Specification"
    )
    pgroup = parent_environment_group.add_mutually_exclusive_group(required=True)
    pgroup.add_argument(
        "--parent-name",
        action="store",
        help="Name of parent environment.",
        metavar="PARENT_ENVIRONMENT",
    )
    pgroup.add_argument(
        "--parent-prefix",
        action="store",
        help="Full path to parent environment location (i.e. prefix).",
        metavar="PARENT_PATH",
    )

    child_environment_group = parser.add_argument_group(
        "Child Environment Specification"
    )
    cgroup = child_environment_group.add_mutually_exclusive_group(required=True)
    cgroup.add_argument(
        "-n",
        "--name",
        action="store",
        help="Name of environment.",
        metavar="CHILD_ENVIRONMENT",
    )
    cgroup.add_argument(
        "-p",
        "--prefix",
        action="store",
        help="Full path to environment location (i.e. prefix).",
        metavar="CHILD_PATH",
    )

    args = parser.parse_args()

    if args.parent_prefix:
        parent_prefix = args.parent_prefix
    else:
        parent_prefix = locate_prefix_by_name(args.parent_name)

    if args.prefix:
        child_prefix = args.prefix
    else:
        child_prefix = locate_prefix_by_name(args.name)

    if not is_conda_environment(parent_prefix):
        raise EnvironmentLocationNotFound(parent_prefix)

    create_empty_child_enviroment(child_prefix, args)
    link_parent_python_to_child(parent_prefix, child_prefix)
    copy_conda_meta(parent_prefix, child_prefix)
    return 0


if __name__ == "__main__":
    main()
