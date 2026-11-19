# Learning guide

The repository is an AI-assisted starter. Work through the code, run the checks,
and record your own modifications to develop a work sample you can explain.

## C# and ASP.NET Core

Begin with `aspnetcore-student-results/Program.cs` and follow one request:

1. `POST /api/results` binds JSON to `ResultRequest`.
2. `Validate` checks the required fields, ID format and score range.
3. `ApplyTo` trims text and creates canonical keys.
4. EF Core writes the row. The unique database index rejects duplicates.
5. The API maps the stored row to `ResultResponse` and returns 201.

Find these concepts from your C# course in the code:

| C# concept | Example |
| --- | --- |
| Classes and properties | `StudentResult` |
| Records | `ResultRequest` and `ResultResponse` |
| Nullable types | `string?`, `int?` and empty-summary averages |
| Collections | Validation error dictionary and result lists |
| LINQ | Filtering, pagination, grouping and aggregation |
| Exceptions | Handling a database uniqueness conflict |
| Async programming | `Task<IResult>`, `await` and cancellation tokens |
| Dependency injection | A database context supplied to each endpoint |

Review questions:

- Why does a database unique index matter when two requests arrive together?
- Why reject a numeric string when the API contract calls for an integer?
- Why does SQLite need explicit UTC handling for these timestamps?
- What should an empty average be, and why?
- Which concerns would authentication and optimistic concurrency address?

Try these changes and keep a short note of what happened:

1. Add a subject filter to the browser interface.
2. Add a configurable pass mark and a test at the exact boundary.
3. Add CSV export of filtered records, with correct CSV escaping.

## TensorFlow

Run the notebook cell by cell. Explain each of these before changing the model:

- Pixel normalisation and input shape.
- Training, validation and test partitions.
- Hidden layers, ReLU, dropout, logits and loss.
- Accuracy compared with a majority-class baseline.
- What the confusion matrix reveals that one accuracy number does not.

Next, change **only one** setting, such as dropout with the hidden width held
fixed. Rerun and write down the validation result, test result, and a limitation
of your comparison. Never invent or copy a benchmark number into your report.

## Explaining this work in an application

Present this as an **AI-assisted learning project**. Separate the supplied starter
from the parts you personally ran, understood, changed and tested. Link the
relevant project folder and describe concrete actions you actually completed.

The ASP.NET Core API supports an ASP.NET Core work sample. The notebook supports
an introductory TensorFlow work sample after you have worked through it. Neither
project is evidence of professional deployment or experience with legacy ASP.NET
Framework.
