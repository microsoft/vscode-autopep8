# Formatter extension for Visual Studio Code using autopep8

A Visual Studio Code extension with support for the autopep8 formatter. The extension ships with `autopep8=2.1.0`.

> Note: The minimum supported version of autopep8 is `1.7.0`. If you have any issues with formatting with autopep8, please report it to [this issue tracker](https://github.com/hhatto/autopep8/issues) as this extension is just a wrapper around autopep8.

This extension supports for all [actively supported versions](https://devguide.python.org/#status-of-python-branches) of the Python language (i.e., Python >= 3.8).

For more information on autopep8, see https://pypi.org/project/autopep8/.


## Usage and Features

The autopep8 extension for Visual Studio Code provides formatting support for your Python files. Check out the [Settings section](#settings) for more details on how to customize this extension.


- **Integrated formatting**: Once this extension is installed in VS Code, autopep8 will be automatically available as a formatter for Python. This is because the extension ships with a autopep8 binary. You can ensure VS Code uses autopep8 by default for all your Python files by setting the following in your User settings (**View** > **Command Palette...** and run **Preferences: Open User Settings (JSON)**):
  ```json
      "[python]": {
        "editor.defaultFormatter": "ms-python.autopep8"
      }
  ```

-   **Format on save**: Automatically format your Python files on save by setting the `editor.formatOnSave` setting to `true` and the `editor.defaultFormatter` setting to `ms-python.autopep8`. You can also enable format on save for Python files only by adding the following to your settings:

    ```json
      "[python]": {
        "editor.defaultFormatter": "ms-python.autopep8",
        "editor.formatOnSave": true
      }
    ```

-   **Customize autopep8**: You can customize the behavior of autopep8 by setting the `autopep8.args` setting.


### Disabling formatting with autopep8

If you want to disable the autopep8 formatter, you can [disable this extension](https://code.visualstudio.com/docs/editor/extension-marketplace#_disable-an-extension) per workspace in Visual Studio Code.

## Settings

There are several settings you can configure to customize the behavior of this extension.

<table>
  <thead>
    <tr>
      <th>Settings</th>
      <th>Default</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>autopep8.args</td>
      <td><code>[]</code></td>
      <td>Arguments passed to autopep8 to format Python files. Each argument should be provided as a separate string in the array. Example: <code>"autopep8.args" = ["--config", "&lt;file&gt;"]</code></td>
    </tr>
    <tr>
      <td>autopep8.cwd</td>
      <td><code>${workspaceFolder}</code></td>
      <td>Sets the current working directory used to format Python files with autopep8. By default, it uses the root directory of the workspace <code>${workspaceFolder}</code>. You can set it to <code>${fileDirname}</code> to use the parent folder of the file being formatted as the working directory for autopep8.</td>
    </tr>
    <tr>
      <td>autopep8.path</td>
      <td><code>[]</code></td>
      <td>Path or command to be used by the extension to format Python files with autopep8. Accepts an array of a single or multiple strings. If passing a command, each argument should be provided as a separate string in the array. If set to <code>["autopep8"]</code>, it will use the version of autopep8 available in the <code>PATH</code> environment variable. Note: Using this option may slowdown formatting. <br> Examples: <br> <code>["~/global_env/autopep8"]</code> <br> <code>["conda", "run", "-n", "lint_env", "python", "-m", "autopep8"]</code></td>
    </tr>
    <tr>
      <td>autopep8.interpreter</td>
      <td><code>[]</code></td>
      <td>Path to a Python executable or a command that will be used to launch the autopep8 server and any subprocess. Accepts an array of a single or multiple strings. When set to <code>[]</code>, the extension will use the path to the selected Python interpreter. If passing a command, each argument should be provided as a separate string in the array.</td>
    </tr>
    <tr>
      <td>autopep8.importStrategy</td>
      <td><code>useBundled</code></td>
      <td>Defines which autopep8 formatter binary to be used to format Python files. When set to <code>useBundled</code>, the extension will use the autopep8 formatter binary that is shipped with the extension. When set to <code>fromEnvironment</code>, the extension will attempt to use the autopep8 formatter binary and all dependencies that are available in the currently selected environment. <br> Note: If the extension can't find a valid autopep8 formatter binary in the selected environment, it will fallback to using the binary that is shipped with the extension. The <code>autopep8.path</code> setting takes precedence and overrides the behavior of <code>autopep8.importStrategy </code>.</td>
    </tr>
    <tr>
      <td>autopep8.showNotification</td>
      <td><code>off</code></td>
      <td>Controls when notifications are shown by this extension. Accepted values are <code>onError</code>, <code>onWarning</code>, <code>always</code> and <code>off</code>.</td>
    </tr>
  </tbody>
</table>

## Commands

| Command           | Description                       |
| ----------------- | --------------------------------- |
| autopep8: Restart | Force re-start the format server. |

## Logging

From the Command Palette (**View** > **Command Palette ...**), run the **Developer: Set Log Level...** command. Select **autopep8** from the **Extension logs** group. Then select the log level you want to set.

Alternatively, you can set the `autopep8.trace.server` setting to `verbose` to get more detailed logs from the autopep8 server. This can be helpful when filing bug reports.

To open the logs, click on the language status icon (`{}`) on the bottom right of the Status bar, next to the Python language mode. Locate the **autopep8** entry and select **Open logs**.

## Troubleshooting

In this section, you will find some common issues you might encounter and how to resolve them. If you are experiencing any issues that are not covered here, please [file an issue](https://github.com/microsoft/vscode-autopep8/issues).

-   If the `autopep8.importStrategy` setting is set to `fromEnvironment` but autopep8 is not found in the selected environment, this extension will fallback to using the autopep8 binary that is shipped with the extension. However, if there are dependencies installed in the environment, those dependencies will be used along with the shipped autopep8 binary. This can lead to problems if the dependencies are not compatible with the shipped autopep8 binary.

    To resolve this issue, you can:

    -   Set the `autopep8.importStrategy` setting to `useBundled` and the `autopep8.path` setting to point to the custom binary of autopep8 you want to use; or
    -   Install autopep8 in the selected environment.