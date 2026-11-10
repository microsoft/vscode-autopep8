# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Tests for bundled server dependencies."""

import os
import subprocess
import sys

from .lsp_test_client import constants

BUNDLED_LIBS = constants.PROJECT_ROOT / "bundled" / "libs"


def test_bundled_server_dependencies_import():
    """Verify the language server imports only from the bundled dependencies."""
    script = """
import pathlib
import sys

bundle = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(bundle))

import cattrs
import pygls.server
import typing_extensions

assert pathlib.Path(typing_extensions.__file__).resolve().is_relative_to(bundle)
"""

    subprocess.run(
        [sys.executable, "-S", "-c", script, os.fspath(BUNDLED_LIBS)],
        check=True,
    )
