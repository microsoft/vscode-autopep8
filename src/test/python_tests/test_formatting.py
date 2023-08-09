# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for formatting over LSP.
"""
import copy
import pathlib

from hamcrest import assert_that, is_

from .lsp_test_client import constants, defaults, session, utils

FORMATTER = utils.get_server_info_defaults()
TIMEOUT = 10000  # 10 seconds


def test_formatting():
    """Test formatting a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.python_file(contents, UNFORMATTED_TEST_FILE_PATH.parent) as pf:
        uri = utils.as_uri(str(pf))

        with session.LspSession() as ls_session:
            ls_session.initialize()
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by autopep8
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
        }
    ]

    assert_that(actual, is_(expected))


def test_formatting_cell():
    """Test formating a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.formatted"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []

    # generate a fake cell uri
    uri = (
        utils.as_uri(UNFORMATTED_TEST_FILE_PATH.parent / "sample.ipynb").replace(
            "file:", "vscode-notebook-cell:"
        )
        + "#C00001"
    )

    with session.LspSession() as ls_session:
        ls_session.initialize()
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": uri},
                # `options` is not used by autopep8
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
        }
    ]

    assert_that(actual, is_(expected))


def test_skipping_site_packages_files():
    """Test skipping formatting when the file is in site-packages"""

    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.unformatted"
    with session.LspSession() as ls_session:
        # Use any stdlib path here
        uri = utils.as_uri(pathlib.__file__)
        ls_session.initialize()
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8"),
                }
            }
        )

        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": uri},
                # `options` is not used by black
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    expected = None
    assert_that(actual, is_(expected))


def test_skipping_excluded_files():
    """Test skipping formatting when the file is in excluded pattern"""

    UNFORMATTED_EXCLUDED_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.unformatted"

    contents = UNFORMATTED_EXCLUDED_FILE_PATH.read_text()

    with utils.python_file(contents, UNFORMATTED_EXCLUDED_FILE_PATH.parent) as pf:
        with session.LspSession() as ls_session:
            # Use any stdlib path here
            uri = utils.as_uri(str(pf))

            init_args = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
            init_options = init_args["initializationOptions"]
            init_options["settings"][0]["args"] = ["--exclude=**/*.py"]
            ls_session.initialize(init_args)

            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": UNFORMATTED_EXCLUDED_FILE_PATH.read_text(encoding="utf-8"),
                    }
                }
            )

            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by black
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = None
    assert_that(actual, is_(expected))

    def test_formatting_file_not_in_excluded_files():
        """Test formatting when the file is not in excluded pattern"""
        FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample4" / "sample.py"
        UNFORMATTED_INCLUDED_FILE_PATH = constants.TEST_DATA / "sample4" / "sample.included.unformatted"

        contents = UNFORMATTED_INCLUDED_FILE_PATH.read_text()
        lines = contents.splitlines(keepends=False)

        with utils.python_file(contents, UNFORMATTED_INCLUDED_FILE_PATH.parent) as pf:
            with session.LspSession() as ls_session:
                # Use any stdlib path here
                uri = utils.as_uri(str(pf))

                init_args = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
                init_options = init_args["initializationOptions"]
                init_options["settings"][0]["args"] = ["--exclude=**/*exclude"]
                ls_session.initialize(init_args)

                ls_session.notify_did_open(
                    {
                        "textDocument": {
                            "uri": uri,
                            "languageId": "python",
                            "version": 1,
                            "text": UNFORMATTED_INCLUDED_FILE_PATH.read_text(encoding="utf-8"),
                        }
                    }
                )

                actual = ls_session.text_document_formatting(
                    {
                        "textDocument": {"uri": uri},
                        # `options` is not used by black
                        "options": {"tabSize": 4, "insertSpaces": True},
                    }
                )

        expected = [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": len(lines), "character": 0},
                    },
                "newText": FORMATTED_TEST_FILE_PATH.read_text(),
                }
            ]
        assert_that(actual, is_(expected))

    def test_formatting_file_with_excluded_and_other_args():
        """Test formatting when we have more arguments specified"""
        FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample4" / "sample.py"
        UNFORMATTED_INCLUDED_FILE_PATH = constants.TEST_DATA / "sample4" / "sample.included.unformatted"

        contents = UNFORMATTED_INCLUDED_FILE_PATH.read_text()
        lines = contents.splitlines(keepends=False)

        with utils.python_file(contents, UNFORMATTED_INCLUDED_FILE_PATH.parent) as pf:

            with session.LspSession() as ls_session:
                # Use any stdlib path here
                uri = utils.as_uri(str(pf))

                init_args = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
                init_options = init_args["initializationOptions"]
                init_options["settings"][0]["args"] = ["--exclude=**/*exclude", "--aggressive"]
                ls_session.initialize(init_args)

                ls_session.notify_did_open(
                    {
                        "textDocument": {
                            "uri": uri,
                            "languageId": "python",
                            "version": 1,
                            "text": UNFORMATTED_INCLUDED_FILE_PATH.read_text(encoding="utf-8"),
                        }
                    }
                )

                actual = ls_session.text_document_formatting(
                    {
                        "textDocument": {"uri": uri},
                        # `options` is not used by black
                        "options": {"tabSize": 4, "insertSpaces": True},
                    }
                )

        expected = [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": len(lines), "character": 0},
                    },
                "newText": FORMATTED_TEST_FILE_PATH.read_text(),
                }
            ]
        assert_that(actual, is_(expected))
