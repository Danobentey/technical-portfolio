"""Validate notebook structure, executable Python cells and saved result consistency."""

import ast
import json
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
notebook = nbformat.read(ROOT / "tensorflow-digit-classifier/mnist_classifier.ipynb", as_version=4)
nbformat.validate(notebook)
code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
for cell in code_cells:
    ast.parse(cell.source)
    assert cell.execution_count is not None, "Commit the executed notebook."
    assert all(output.output_type != "error" for output in cell.outputs), "An execution error was committed."

metrics = json.loads((ROOT / "tensorflow-digit-classifier/results/metrics.json").read_text())
assert len(metrics["experiments"]) == 2
assert metrics["split"]["train"] == 12000
assert metrics["split"]["validation"] == 3000
assert metrics["split"]["test"] == 10000
assert sum(sum(row) for row in metrics["confusion_matrix"]) == metrics["split"]["test"]
correct = sum(metrics["confusion_matrix"][digit][digit] for digit in range(10))
assert abs(correct / metrics["split"]["test"] - metrics["test_accuracy"]) < 1e-6
assert metrics["selected_model"] in {row["name"] for row in metrics["experiments"]}
print(f"Validated {len(code_cells)} executed cells and saved experiment metrics.")
