"""
Test for path and interpreter settings.
"""

import copy
import os
import pathlib
import sys

from hamcrest import assert_that, is_

from .lsp_test_client import constants, defaults, session, utils

FORMATTER = utils.get_server_info_defaults()
TIMEOUT = 10  # 10 seconds
TEST_FILE = constants.TEST_DATA / "sample1" / "sample.py"
UTILS_PATH = (
    pathlib.Path(__file__).parent.parent.parent.parent / "bundled" / "lib" / "autopep8"
)


class CallbackObject:
    """Object that holds results for WINDOW_LOG_MESSAGE to capture argv"""

    def __init__(self):
        self.result = False

    def check_result(self):
        """returns Boolean result"""
        return self.result

    def check_for_argv_duplication(self, argv):
        """checks if argv duplication exists and sets result boolean"""
        message = argv["message"].split()
        duplicate_stdin = message.count("-") > 1
        duplicate_version = "--version" in message and "-" in message
        if argv["type"] == 4 and (duplicate_stdin or duplicate_version):
            self.result = True

    def check_for_recursive_removal(self, argv):
        """checks if recursive removal exists and sets result boolean"""
        recursive = "Removing --recursive" in argv["message"]
        if recursive:
            self.result = True


def test_path():
    """Test formatting using autopep8 bin path set."""

    init_params = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
    init_params["initializationOptions"]["settings"][0]["path"] = [
        sys.executable,
        os.fspath(UTILS_PATH),
    ]

    argv_callback_object = CallbackObject()
    contents = TEST_FILE.read_text()

    actual = []
    with utils.python_file(contents, TEST_FILE.parent) as file:
        uri = utils.as_uri(str(file))

        with session.LspSession() as ls_session:
            ls_session.set_notification_callback(
                session.WINDOW_LOG_MESSAGE,
                argv_callback_object.check_for_argv_duplication,
            )

            ls_session.initialize(init_params)
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

            # Call this second time to detect arg duplication.
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

            ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by black
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

            actual = argv_callback_object.check_result()

    assert_that(actual, is_(False))


def test_args_recursive():
    """Test formatting using --recursive in args."""

    init_params = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
    init_params["initializationOptions"]["settings"][0]["args"] = [
        "--recursive",
    ]

    argv_callback_object = CallbackObject()
    contents = TEST_FILE.read_text()

    actual = []
    with utils.python_file(contents, TEST_FILE.parent) as file:
        uri = utils.as_uri(str(file))

        with session.LspSession() as ls_session:
            ls_session.set_notification_callback(
                session.WINDOW_LOG_MESSAGE,
                argv_callback_object.check_for_recursive_removal,
            )

            ls_session.initialize(init_params)
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

            # Call this second time to detect arg duplication.
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

            ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by black
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

            actual = argv_callback_object.check_result()

    assert_that(actual, is_(True))


def test_interpreter():
    """Test formatting using specific python path."""
    init_params = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
    init_params["initializationOptions"]["settings"][0]["interpreter"] = ["python"]

    argv_callback_object = CallbackObject()
    contents = TEST_FILE.read_text()

    actual = []
    with utils.python_file(contents, TEST_FILE.parent) as file:
        uri = utils.as_uri(str(file))

        with session.LspSession() as ls_session:
            ls_session.set_notification_callback(
                session.WINDOW_LOG_MESSAGE,
                argv_callback_object.check_for_argv_duplication,
            )

            ls_session.initialize(init_params)
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

            # Call this second time to detect arg duplication.
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

            actual = argv_callback_object.check_result()

    assert_that(actual, is_(False))
