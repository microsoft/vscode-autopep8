# Formatter extension for Visual Studio Code using `autopep8`

A Visual Studio Code extension with support for the `autopep8` formatter. The extension ships with `autopep8=2.0.4`.

Note:

-   This extension is supported for all [actively supported versions](https://devguide.python.org/#status-of-python-branches) of the Python language (i.e., Python >= 3.8).
-   The bundled `autopep8` is only used if there is no installed version of `autopep8` found in the selected Python environment.
-   Minimum supported version of `autopep8` is `1.7.0`.
-   This extension is experimental. The plan is that it will eventually replace the `autopep8` formatting functionality of [the Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

## Usage

Once installed in Visual Studio Code, "autopep8" will be available as a formatter for Python files. Please select "autopep8" (extension id:`ms-python.autopep8`) as the default formatter. You can do this either by using the context menu (right click on a open Python file in the editor) and select "Format Document With...", or you can add the following to your settings:

```json
  "[python]": {
    "editor.defaultFormatter": "ms-python.autopep8"
  }
```

and change the following, if set:

```json
  "python.formatting.provider": "none"
```

### Format on save

You can enable format on save for Python by having the following values in your settings:

```json
  "[python]": {
    "editor.defaultFormatter": "ms-python.autopep8",
    "editor.formatOnSave": true
  }
```

### Disabling formatting with `autopep8`

If you want to disable autopep8 formatter, you can [disable this extension](https://code.visualstudio.com/docs/editor/extension-marketplace#_disable-an-extension) per workspace in Visual Studio Code.

## Settings

| Settings                  | Default      | Description                                                                                                                                                                                                                                                                          |
| ------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| autopep8.args             | `[]`         | Custom arguments passed to `autopep8`. E.g `"autopep8.args" = ["--global-config", "<file>"]`                                                                                                                                                                                         |
| autopep8.path             | `[]`         | Setting to provide custom `autopep8` executable. This will slow down formatting, since we will have to run `autopep8` executable every time or file save or open. Example 1: `["~/global_env/autopep8"]` Example 2: `["conda", "run", "-n", "lint_env", "python", "-m", "autopep8"]` |
| autopep8.interpreter      | `[]`         | Path to a Python interpreter to use to run the formatter server. When set to `[]`, the interpreter for the workspace is obtained from `ms-python.python` extension. If set to some path, that path takes precedence, and the Python extension is not queried for the interpreter     |
| autopep8.importStrategy   | `useBundled` | Setting to choose where to load `autopep8` from. `useBundled` picks autopep8 bundled with the extension. `fromEnvironment` uses `autopep8` available in the environment.                                                                                                             |
| autopep8.showNotification | `off`        | Setting to control when a notification is shown.                                                                                                                                                                                                                                     |

## Commands

| Command           | Description                       |
| ----------------- | --------------------------------- |
| autopep8: Restart | Force re-start the format server. |

## Logging

Use `Developer : Set Log Level...` command from the **Command Palette**, and select `autopep8` from the extensions list to set the Log Level for the extension. For detailed LSP traces, add `"autopep8.trace.server" : "verbose"` to your **User** `settings.json` file.
