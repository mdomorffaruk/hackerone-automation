
import subprocess
import os

def run_tool(command, output_file=None):
    """
    Runs a shell command and optionally saves the output to a file.

    Args:
        command (str or list): The command to run.
        output_file (str, optional): The file to save the output to. Defaults to None.

    Returns:
        str: The output of the command.
    """
    if isinstance(command, str):
        command = command.split()

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        output = process.stdout

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)

        return output
    except FileNotFoundError as e:
        print(f"Error: {command[0]} not found. Please make sure it is installed and in your PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running {command[0]}: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def create_dir(directory):
    """
    Creates a directory if it doesn't exist.

    Args:
        directory (str): The directory to create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
