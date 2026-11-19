# Student Results API

A small ASP.NET Core application with a browser interface and a persistent SQLite
database. It stores **one score per student and subject** and calculates summary
statistics. All examples use synthetic student IDs.

## Start

Requirements: .NET 10 SDK. From the repository root:

```bash
dotnet restore aspnetcore-student-results --locked-mode
dotnet run --project aspnetcore-student-results --urls http://127.0.0.1:5000
```

Open http://127.0.0.1:5000. The browser interface adds, lists and deletes results,
and displays aggregate metrics. The API also supports updates and filters.

The default database lives at `aspnetcore-student-results/data/student-results.db`
when launched with the command above. Database files are excluded from Git. To
select another database, set the ASP.NET configuration environment variable
`ConnectionStrings__Results`, for example `Data Source=/absolute/path/results.db`.
The parent directory must exist when using a custom connection string.

## Endpoints

| Method | Path | Behaviour |
| --- | --- | --- |
| GET | `/health` | Process health |
| GET | `/api/results` | Paginated results; optional `studentId` and `subject` filters |
| GET | `/api/results/{id}` | One result, or 404 |
| POST | `/api/results` | Create a result; returns 201 with a Location header |
| PUT | `/api/results/{id}` | Replace the result's editable fields |
| DELETE | `/api/results/{id}` | Delete a result; returns 204, or 404 if missing |
| GET | `/api/results/summary` | Counts, average, pass rate and per-subject aggregates; supports the same filters |

`page` defaults to 1, and `pageSize` defaults to 20. The maximum page size is 100.
Student and subject filters are exact matches after trimming and normalisation.

## Request example

```json
{
  "studentId": "STU001",
  "subject": "Mathematics",
  "score": 78
}
```

- `studentId`: 1–32 ASCII letters, digits, underscores or hyphens; first character
  must be a letter or digit. Surrounding whitespace is removed; IDs are uppercased.
- `subject`: 1–80 characters after trimming. A separate uppercase key enforces
  case-insensitive uniqueness without changing the display text.
- `score`: a JSON integer from 0 to 100. Numeric strings, booleans, fractions and
  missing scores are rejected with 400.
- A score of 50 or above is a pass in this demo.
- A duplicate student/subject pair returns 409, including competing create requests.
- Invalid input returns a validation-problem response. Timestamps are UTC.

### Windows PowerShell

```powershell
$body = @{ studentId = "STU001"; subject = "Mathematics"; score = 78 } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/results -Method Post -ContentType application/json -Body $body
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/results/summary
```

### Update and filter

Replace `1` with the ID returned when you created a result:

```bash
curl -X PUT http://127.0.0.1:5000/api/results/1 \
  -H "Content-Type: application/json" \
  -d '{"studentId":"STU001","subject":"Mathematics","score":85}'
curl "http://127.0.0.1:5000/api/results?studentId=stu001&page=1&pageSize=10"
curl "http://127.0.0.1:5000/api/results/summary?subject=mathematics"
```

Empty summaries return `null` for the average and pass rate, since no observations
exist. The average weights every result equally; it is not a per-student GPA.

## Code tour

| File | Responsibility |
| --- | --- |
| `Program.cs` | Configure services, SQLite, static files and routes |
| `Models.cs` | Request validation, canonical keys and response data |
| `ResultsDbContext.cs` | Table mapping, uniqueness, score constraint and UTC conversion |
| `ResultsEndpoints.cs` | HTTP behaviour, pagination and database queries |
| `wwwroot/` | Small vanilla JavaScript interface |
| `../tests/api_integration.py` | Integration tests against a real process and database |

The unique database index handles duplicate races. Each create or update uses
EF Core's normal save transaction. Summaries use a short read transaction so
their component queries describe a consistent database snapshot.

## Tests

From the repository root, with `dotnet` and Python 3 on PATH:

```bash
python tests/api_integration.py
```

The suite covers CRUD, invalid types and ranges, normalisation, duplicate races,
failed update rollback, filtering, pagination, pass boundaries, empty summaries,
and persistence across a server restart. It creates and removes its own temporary
database, leaving your demo data untouched. Set `DOTNET` to an absolute executable
path if your SDK is not on PATH.

## Limits and next steps

- This demo has no authentication and should remain on localhost with synthetic data.
- `EnsureCreated` creates the initial schema. Introduce migrations before changing
  an existing database schema.
- SQLite serialises writes. A service with sustained concurrent writes needs a
  database and deployment design appropriate to its workload.
- The API does not implement optimistic concurrency. Two updates to the same
  result follow last-write-wins behaviour.
- The interface shows the first 100 records; use the API for pagination and filters.

Suggested extension: add a subject filter to the browser interface, then add an
integration test showing that its summary uses the same filter as its list.
