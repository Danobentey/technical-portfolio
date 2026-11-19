"""Execute the notebook through IPython and save actual outputs in place.

Running in process avoids requiring a separate Jupyter server or kernel sockets.
The notebook also runs normally in Jupyter or Google Colab.
"""

from pathlib import Path
import os
import sys

import nbformat
from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.utils.capture import capture_output

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "tensorflow-digit-classifier/mnist_classifier.ipynb"


def main():
    os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
    os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    shell = TerminalInteractiveShell.instance()
    shell.enable_matplotlib("inline")
    shell.display_formatter.active_types = ["text/plain", "image/png", "image/svg+xml", "text/html"]
    original_directory = Path.cwd()
    try:
        os.chdir(NOTEBOOK.parent)
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            execution_count = shell.execution_count
            with capture_output() as captured:
                result = shell.run_cell(cell.source, store_history=True)
            if result.error_before_exec or result.error_in_exec:
                print(captured.stdout)
                print(captured.stderr, file=sys.stderr)
                raise RuntimeError("Notebook execution failed.") from (result.error_before_exec or result.error_in_exec)
            outputs = []
            if captured.stdout:
                outputs.append(nbformat.v4.new_output("stream", name="stdout", text=captured.stdout))
            if captured.stderr:
                outputs.append(nbformat.v4.new_output("stream", name="stderr", text=captured.stderr))
            for output in captured.outputs:
                outputs.append(nbformat.v4.new_output("display_data", data=output.data, metadata=output.metadata))
            cell.execution_count = execution_count
            cell.outputs = outputs
            print(f"Executed cell {execution_count}", flush=True)
    finally:
        os.chdir(original_directory)
    for figure in (NOTEBOOK.parent / "results").glob("*.svg"):
        figure.write_text("\n".join(line.rstrip() for line in figure.read_text().splitlines()) + "\n", encoding="utf-8")
    # Publish executed output only when every cell has finished successfully.
    nbformat.write(notebook, NOTEBOOK)
    print(f"Executed and saved {NOTEBOOK.relative_to(ROOT)} using {sys.executable}")


if __name__ == "__main__":
    main()
