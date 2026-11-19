# technical-portfolio

Two AI-assisted learning projects for practising **C#, ASP.NET Core, SQL databases,
and TensorFlow**. Each example includes executable code, explanations and checks.

| Work sample | What it demonstrates | Start here |
| --- | --- | --- |
| Student Results API | ASP.NET Core Minimal APIs, SQLite/EF Core, validation, REST endpoints, aggregation and a browser interface | [API guide](aspnetcore-student-results/README.md) |
| Handwritten digit classifier | TensorFlow/Keras, preprocessing, validation-based model selection, test evaluation and error analysis | [Executed notebook](tensorflow-digit-classifier/mnist_classifier.ipynb) · [ML guide](tensorflow-digit-classifier/README.md) |

## Run the API

Install the **.NET 10 SDK**, then run from this repository's root:

```bash
dotnet run --project aspnetcore-student-results --urls http://127.0.0.1:5000
```

Open **http://127.0.0.1:5000** to add synthetic results and view the summary.
The SQLite database is created automatically and persists between restarts.

```bash
curl http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/api/results \
  -H "Content-Type: application/json" \
  -d '{"studentId":"STU001","subject":"Mathematics","score":78}'
curl http://127.0.0.1:5000/api/results/summary
```

On Windows PowerShell, use `curl.exe` or the `Invoke-RestMethod` examples in the
[API guide](aspnetcore-student-results/README.md).

## Run the TensorFlow notebook

[Open in Google Colab](https://colab.research.google.com/github/Danobentey/technical-portfolio/blob/main/tensorflow-digit-classifier/mnist_classifier.ipynb)
and select **Runtime → Run all**. The notebook is self-contained; the first run
downloads MNIST. A CPU runtime is enough. Colab uses its installed packages and
prints their versions.

For a local run, create and activate a Python 3.12 virtual environment, then:

```bash
python -m pip install -r tensorflow-digit-classifier/requirements.txt
python scripts/execute_notebook.py
python scripts/check_notebook.py
```

The execution helper runs the cells through IPython in process, captures their
real outputs and saves the notebook only after every cell succeeds. It also
writes metrics, plots and a local model under `tensorflow-digit-classifier/results/`.

## Verify the projects

```bash
# Starts a real API with a temporary SQLite database and runs 12 integration tests.
python tests/api_integration.py

# Checks executed notebook cells and consistency of saved evaluation metrics.
python scripts/check_notebook.py
```

See [verification results](docs/VERIFICATION.md) for the environment and measured
outputs. GitHub Actions runs API integration tests and notebook validation on push
and pull requests. A manual workflow run also retrains the notebook.

## Learn and extend

Read the [learning guide](docs/LEARNING_GUIDE.md) for a code tour, review questions,
and small extension exercises. The API and classifier are **separate work samples**;
the classifier does not predict student performance or connect to the API.

**Authorship:** the starter implementation and documentation were generated with
ChatGPT/Codex assistance. Saved checks and model metrics record automated execution.
Use the exercises to develop and demonstrate your own understanding and changes.

## Scope

The API is a local learning demo with no authentication, rate limiting or
multi-user access controls. Use synthetic records. Its pass mark of 50 is a demo
rule. The classifier evaluates a benchmark dataset; its accuracy does not establish
performance on images collected elsewhere.

## References

- [Microsoft: Create a Minimal API with ASP.NET Core](https://learn.microsoft.com/en-us/aspnet/core/tutorials/min-web-api?view=aspnetcore-10.0)
- [TensorFlow: Beginner quickstart](https://www.tensorflow.org/tutorials/quickstart/beginner)
- [Keras: MNIST dataset and provenance](https://keras.io/api/datasets/mnist/)

The tutorials are learning references; this repository adds its own application
scenario, validation, persistence, tests and model-comparison workflow. Dependency
and dataset licences remain with their respective owners.
