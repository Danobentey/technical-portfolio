# Verification results

These results were measured by automated verification on 19 November 2026.
They describe this run and environment, rather than a promise of future accuracy.

## ASP.NET Core API

- .NET SDK: **10.0.404**; target framework: **net10.0**.
- EF Core SQLite package: **10.0.15**, with a committed NuGet lock file.
- Release build: **passed, zero warnings and zero errors**.
- HTTP integration suite: **12 tests passed** against a real process and temporary SQLite database.
- Covered CRUD, input types and bounds, normalised duplicate keys, conflicting
  updates, aggregates, pagination, filtered summaries, missing records, concurrent
  duplicate requests and persistence after restart.
- JavaScript syntax check: **passed**.

Run the integration suite yourself:

```bash
python tests/api_integration.py
```

## TensorFlow experiment

- Python: **3.12.14**.
- TensorFlow: **2.20.0**; Keras: **3.15.1**; NumPy: **2.5.5**.
- Device: **CPU**; seed: **42**.
- Training: **12,000** images; validation: **3,000**; held-out test: **10,000**.
- The remaining 45,000 examples from the original training partition were unused.
- Each candidate trained for **5 epochs**, with batch size **128**.

| Candidate | Validation accuracy | Validation loss | Epochs |
| --- | ---: | ---: | ---: |
| dense_64 | 93.13% | 0.2438 | 5 |
| dense_128_dropout | 94.40% | 0.2050 | 5 |

Selected on validation data: **dense_128_dropout**.

- Held-out test accuracy: **94.14%**.
- Held-out test loss: **0.2016**.
- Majority-class baseline test accuracy: **11.35%**.
- Notebook execution: **all 6 code cells completed**, with real text and plot outputs saved.
- Notebook validation and saved-metrics consistency checks: **passed**.

The final evaluation used the original MNIST test set, after selecting the model
on validation data. Both model width and dropout differ between the candidates;
this run does not isolate the effect of either variable. The notebook's metrics
file contains the confusion matrix and full measured values.

- [Executed notebook](../tensorflow-digit-classifier/mnist_classifier.ipynb)
- [Machine-readable metrics](../tensorflow-digit-classifier/results/metrics.json)
- [Learning curves](../tensorflow-digit-classifier/results/training.svg)
- [Confusion matrix](../tensorflow-digit-classifier/results/confusion-matrix.svg)
- [Example errors](../tensorflow-digit-classifier/results/prediction-errors.svg)

Re-execution updates the notebook and metrics. Update this report if you publish
a new measured run. Rounding to two decimal places in this report is for display.
