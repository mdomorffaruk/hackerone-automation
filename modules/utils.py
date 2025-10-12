
import subprocess
import os

def run_tool(command, output_file=None, app=None, tool_name=None, verbose=0):
    """
    Runs a shell command and optionally saves the output to a file.

    Args:
        command (str or list): The command to run.
        output_file (str, optional): The file to save the output to. Defaults to None.
        app (AutomateApp, optional): The Textual app instance. Defaults to None.
        tool_name (str, optional): The name of the tool. Defaults to None.
        verbose (int, optional): The verbosity level. Defaults to 0.

    Returns:
        str: The output of the command.
    """
    if isinstance(command, str):
        command = command.split()

    if verbose >= 1 and app and tool_name:
        app.call_from_thread(app.update_tool_log, tool_name, f"$ {' '.join(command)}\n")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = ""
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                output += line
                if verbose >= 2 and app and tool_name:
                    app.call_from_thread(app.update_tool_log, tool_name, line)
        process.wait()

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)

        return output
    except FileNotFoundError as e:
        error_msg = f"Error: {command[0]} not found. Please make sure it is installed and in your PATH."
        if app and tool_name:
            app.call_from_thread(app.update_tool_log, tool_name, error_msg)
        else:
            print(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error running {command[0]}: {e}"
        if app and tool_name:
            app.call_from_thread(app.update_tool_log, tool_name, error_msg)
        else:
            print(error_msg)
        return None

def create_dir(directory):
    """
    Creates a directory if it doesn't exist.

    Args:
        directory (str): The directory to create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
