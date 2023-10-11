# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Implementation of tool support over LSP."""
from __future__ import annotations

import argparse
import ast
import copy
import fnmatch
import json
import os
import pathlib
import sys
import traceback
from typing import Any, Dict, List, Optional, Sequence


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        else:
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
BUNDLE_DIR = pathlib.Path(__file__).parent.parent
# Always use bundled server files.
update_sys_path(os.fspath(BUNDLE_DIR / "tool"), "useBundled")
update_sys_path(
    os.fspath(BUNDLE_DIR / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)


import lsp_edit_utils as edit_utils
# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error
import lsp_jsonrpc as jsonrpc
import lsp_utils as utils
from lsprotocol import types as lsp
from pygls import server, uris, workspace

WORKSPACE_SETTINGS = {}
GLOBAL_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "lsp_runner.py"

MAX_WORKERS = 5
LSP_SERVER = server.LanguageServer(name="autopep8-server", version="1.0.0", max_workers=MAX_WORKERS)


# **********************************************************
# Tool specific code goes below this.
# **********************************************************
TOOL_MODULE = "autopep8"
TOOL_DISPLAY = "autopep8"

# Default arguments always passed to autopep8.
TOOL_ARGS = []

# Minimum version of autopep8 supported.
MIN_VERSION = "1.7.0"

# **********************************************************
# Formatting features start here
# **********************************************************


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(params: lsp.DocumentFormattingParams) -> Optional[List[lsp.TextEdit]]:
    """LSP handler for textDocument/formatting request."""

    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
    return _formatting_helper(document)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_RANGE_FORMATTING)
def range_formatting(params: lsp.DocumentRangeFormattingParams) -> Optional[List[lsp.TextEdit]]:
    """LSP handler for textDocument/formatting request."""

    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
    return _formatting_helper(document, params.range)


def is_python(code: str) -> bool:
    """Ensures that the code provided is python."""
    try:
        ast.parse(code)
    except SyntaxError:
        log_error(f"Syntax error in code: {traceback.format_exc()}")
        return False
    return True


def _formatting_helper(document: workspace.Document, range: Optional[lsp.Range] = None) -> Optional[List[lsp.TextEdit]]:
    extra_args = []
    if range:
        extra_args += ["--line-range", f"{range.start.line + 1}", f"{range.end.line + 1}"]

    result = _run_tool_on_document(document, use_stdin=True, extra_args=extra_args)

    if result and result.stdout:
        if LSP_SERVER.lsp.trace == lsp.TraceValues.Verbose:
            log_to_output(
                f"{document.uri} :\r\n"
                + ("*" * 100)
                + "\r\n"
                + f"{result.stdout}\r\n"
                + ("*" * 100)
                + "\r\n"
            )

        new_source = _match_line_endings(document, result.stdout)

        # Skip last line ending in a notebook cell
        if document.uri.startswith("vscode-notebook-cell"):
            if new_source.endswith("\r\n"):
                new_source = new_source[:-2]
            elif new_source.endswith("\n"):
                new_source = new_source[:-1]

        # If code is already formatted, then no need to send any edits.
        if new_source != document.source:
            edits = edit_utils.get_text_edits(document.source, new_source)
            if edits:
                # NOTE: If you provide [] array, VS Code will clear the file of all contents.
                # To indicate no changes to file return None.
                return edits
    return None


def _get_line_endings(lines: list[str]) -> str:
    """Returns line endings used in the text."""
    try:
        if lines[0][-2:] == "\r\n":
            return "\r\n"
        return "\n"
    except Exception:  # pylint: disable=broad-except
        return None


def _match_line_endings(document: workspace.Document, text: str) -> str:
    """Ensures that the edited text line endings matches the document line endings."""
    expected = _get_line_endings(document.source.splitlines(keepends=True))
    actual = _get_line_endings(text.splitlines(keepends=True))
    if actual == expected or actual is None or expected is None:
        return text
    return text.replace(actual, expected)

# **********************************************************
# Formatting features ends here
# **********************************************************


# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    log_to_output(f"CWD Server: {os.getcwd()}")

    paths = "\r\n   ".join(sys.path)
    log_to_output(f"sys.path used to run Server:\r\n   {paths}")

    _workaround_for_autopep8_reload_issue()
    log_to_output(f"PYTHONPATH env variable used to run Server:\r\n   {os.environ.get('PYTHONPATH', '')}")

    GLOBAL_SETTINGS.update(**params.initialization_options.get("globalSettings", {}))

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )
    log_to_output(
        f"Global settings:\r\n{json.dumps(GLOBAL_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )



    _log_version_info()

    _log_version_info()


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    jsonrpc.shutdown_json_rpc()


def _log_version_info() -> None:
    for value in WORKSPACE_SETTINGS.values():
        try:
            from packaging.version import parse as parse_version

            settings = copy.deepcopy(value)
            result = _run_tool(["--version"], settings)
            code_workspace = settings["workspaceFS"]
            log_to_output(
                f"Version info for formatter running for {code_workspace}:\r\n{result.stdout}"
            )

            if "The typed_ast package is required but not installed" in result.stdout:
                log_to_output(
                    'Install autopep8 in your environment and set "autopep8.importStrategy": "fromEnvironment"'
                )

            # This is text we get from running `autopep8 --version`
            # autopep8 1.7.0 (pycodestyle: 2.9.1) <--- This is the version we want.
            first_line = result.stdout.splitlines(keepends=False)[0]
            actual_version = first_line.split(" ")[1]

            version = parse_version(actual_version)
            min_version = parse_version(MIN_VERSION)

            if version < min_version:
                log_error(
                    f"Version of formatter running for {code_workspace} is NOT supported:\r\n"
                    f"SUPPORTED {TOOL_MODULE}>={min_version}\r\n"
                    f"FOUND {TOOL_MODULE}=={actual_version}\r\n"
                )
            else:
                log_to_output(
                    f"SUPPORTED {TOOL_MODULE}>={min_version}\r\n"
                    f"FOUND {TOOL_MODULE}=={actual_version}\r\n"
                )
        except:  # pylint: disable=bare-except
            log_to_output(
                f"Error while detecting autopep8 version:\r\n{traceback.format_exc()}"
            )


# *****************************************************
# Internal functional and settings management APIs.
# *****************************************************
def _get_global_defaults():
    settings = {
        "path": GLOBAL_SETTINGS.get("path", [sys.executable, "-m", TOOL_MODULE]),
        "interpreter": GLOBAL_SETTINGS.get("interpreter", [sys.executable]),
        "args": GLOBAL_SETTINGS.get("args", []),
        "importStrategy": GLOBAL_SETTINGS.get("importStrategy", "useBundled"),
        "showNotifications": GLOBAL_SETTINGS.get("showNotifications", "off"),
    }
    if not settings["path"]:
        # workaround for reload issue with autopep8
        # https://github.com/hhatto/autopep8/issues/625
        settings["path"] = [
            sys.executable,
            "-m",
            TOOL_MODULE,
        ]
    return settings


def _update_workspace_settings(settings):
    if not settings:
        key = utils.normalize_path(os.getcwd())
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }
        return

    for setting in settings:
        key = utils.normalize_path(uris.to_fs_path(setting["workspace"]))
        WORKSPACE_SETTINGS[key] = {
            **setting,
            "workspaceFS": key,
        }
        if not WORKSPACE_SETTINGS[key]["path"]:
            # workaround for reload issue with autopep8
            # https://github.com/hhatto/autopep8/issues/625
            WORKSPACE_SETTINGS[key]["path"] = [
                sys.executable,
                "-m",
                TOOL_MODULE,
            ]

def _get_settings_by_path(file_path: pathlib.Path):
    workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

    while file_path != file_path.parent:
        str_file_path = utils.normalize_path(file_path)
        if str_file_path in workspaces:
            return WORKSPACE_SETTINGS[str_file_path]
        file_path = file_path.parent

    setting_values = list(WORKSPACE_SETTINGS.values())
    return setting_values[0]


def _get_document_key(document: workspace.Document):
    if WORKSPACE_SETTINGS:
        document_workspace = pathlib.Path(document.path)
        workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

        # Find workspace settings for the given file.
        while document_workspace != document_workspace.parent:
            norm_path = utils.normalize_path(document_workspace)
            if norm_path in workspaces:
                return norm_path
            document_workspace = document_workspace.parent

    return None


def _get_settings_by_document(document: Optional[workspace.Document]):
    if document is None or document.path is None:
        return list(WORKSPACE_SETTINGS.values())[0]

    key = _get_document_key(document)
    if key is None:
        # This is either a non-workspace file or there is no workspace.
        key = utils.normalize_path(pathlib.Path(document.path).parent)
        return {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }

    return WORKSPACE_SETTINGS[str(key)]

def _workaround_for_autopep8_reload_issue():
    # workaround for reload issue with autopep8
    # https://github.com/hhatto/autopep8/issues/625
    lib_path = os.fspath(pathlib.Path(__file__).parent.parent / "libs")
    python_path = os.environ.get('PYTHONPATH', '')
    if os.getenv("LS_IMPORT_STRATEGY", "useBundled") == "useBundled":
        os.environ.update(PYTHONPATH=lib_path + os.pathsep + python_path)
    else:
        try:
            import autopep8  # noqa
        except ImportError:
            os.environ.update(PYTHONPATH=lib_path + os.pathsep + python_path)


# *****************************************************
# Internal execution APIs.
# *****************************************************
# pylint: disable=too-many-branches
def _run_tool_on_document(
    document: workspace.Document,
    use_stdin: bool = False,
    extra_args: Sequence[str] = [],
) -> Optional[utils.RunResult]:
    """Runs tool on the given document.

    if use_stdin is true then contents of the document is passed to the
    tool via stdin.
    """
    if utils.is_stdlib_file(document.path):
        log_warning(f"Skipping standard library file: {document.path}")
        return None

    if not is_python(document.source):
        log_warning(f"Skipping non python code: {document.path}")
        return None

    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(document))

    code_workspace = settings["workspaceFS"]
    cwd = settings["cwd"]

    use_path = False
    use_rpc = False
    if settings["path"]:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif settings["interpreter"] and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += TOOL_ARGS + settings["args"] + extra_args

    if use_stdin:
        exclude_arg, remaining_arg_list = _parse_autopep_exclude_arg(argv)

        if _is_file_in_excluded_pattern(document.path, exclude_arg):
            log_to_output(f"Excluded file: {document.path} because it matches pattern in args")
            return None

        argv = remaining_arg_list
        argv += ["-"]

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source.replace("\r\n", "\n"),
            env={
                "PYTHONUTF8": "1",
            }
        )
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")

        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source,
            env={
                "LS_IMPORT_STRATEGY": settings["importStrategy"],
                "PYTHONUTF8": "1",
            },
        )
        result = _to_run_result_with_logging(result)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", [""] + sys.path[:]):
            try:
                result = utils.run_module(
                    module=TOOL_MODULE,
                    argv=argv,
                    use_stdin=use_stdin,
                    cwd=cwd,
                    source=document.source,
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    return result


def _run_tool(extra_args: Sequence[str], settings: Dict[str, Any]) -> utils.RunResult:
    """Runs tool."""
    code_workspace = settings["workspaceFS"]
    cwd = settings["cwd"]

    use_path = False
    use_rpc = False
    if len(settings["path"]) > 0:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif len(settings["interpreter"]) > 0 and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += extra_args

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(
            argv=argv,
            use_stdin=True,
            cwd=cwd,
            env={
                "PYTHONUTF8": "1",
            })
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")
        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=True,
            cwd=cwd,
            env={
                "LS_IMPORT_STRATEGY": settings["importStrategy"],
                "PYTHONUTF8": "1",
            },
        )
        result = _to_run_result_with_logging(result)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", [""] + sys.path[:]):
            try:
                result = utils.run_module(
                    module=TOOL_MODULE, argv=argv, use_stdin=True, cwd=cwd
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    if LSP_SERVER.lsp.trace == lsp.TraceValues.Verbose:
        log_to_output(f"\r\n{result.stdout}\r\n")

    return result


def _to_run_result_with_logging(rpc_result: jsonrpc.RpcRunResult) -> utils.RunResult:
    error = ""
    if rpc_result.exception:
        log_error(rpc_result.exception)
        error = rpc_result.exception
    elif rpc_result.stderr:
        log_to_output(rpc_result.stderr)
        error = rpc_result.stderr
    return utils.RunResult(rpc_result.stdout, error)


def _is_file_in_excluded_pattern(file_path: str, exclude_arg) -> bool:
    if exclude_arg.exclude is not None:
        exclude_string = ', '.join(exclude_arg.exclude)
        exclude_patterns = _split_comma_separated(exclude_string)

        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True

    return False


def _parse_autopep_exclude_arg(
    argv: list(str)
):
    parser = argparse.ArgumentParser(
        description="Exclude Argument Parser"
    )

    parser.add_argument(
        "--exclude",
        metavar='globs',
        nargs='*',
        required=False
    )

    exclude_argument, remaining_arg_list = parser.parse_known_args(argv)

    return exclude_argument, remaining_arg_list

def _split_comma_separated(string: str):
    """Return a set of strings."""
    return {text.strip() for text in string.split(',') if text.strip()}


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(
    message: str, msg_type: lsp.MessageType = lsp.MessageType.Log
) -> None:
    """Logs messages to Output > autopep8 channel only."""
    LSP_SERVER.show_message_log(message, msg_type)


def log_error(message: str) -> None:
    """Logs messages with notification on error."""
    LSP_SERVER.show_message_log(message, lsp.MessageType.Error)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onError", "onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Error)


def log_warning(message: str) -> None:
    """Logs messages with notification on warning."""
    LSP_SERVER.show_message_log(message, lsp.MessageType.Warning)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Warning)


def log_always(message: str) -> None:
    """Logs messages with notification."""
    LSP_SERVER.show_message_log(message, lsp.MessageType.Info)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Info)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
