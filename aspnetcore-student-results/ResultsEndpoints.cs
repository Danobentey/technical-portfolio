using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace StudentResults.Api;

public static class ResultsEndpoints
{
    public static void MapResultsEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/results");
        group.MapGet("/", List);
        group.MapGet("/summary", Summary);
        group.MapGet("/{id:long}", Get);
        group.MapPost("/", Create);
        group.MapPut("/{id:long}", Update);
        group.MapDelete("/{id:long}", Delete);
    }

    private static IQueryable<StudentResult> Filter(ResultsDbContext db, string? studentId, string? subject)
    {
        var query = db.Results.AsNoTracking();
        if (!string.IsNullOrWhiteSpace(studentId))
        {
            var key = studentId.Trim().ToUpperInvariant();
            query = query.Where(row => row.StudentId == key);
        }
        if (!string.IsNullOrWhiteSpace(subject))
        {
            var key = subject.Trim().ToUpperInvariant();
            query = query.Where(row => row.SubjectKey == key);
        }
        return query;
    }

    private static async Task<IResult> List(ResultsDbContext db, string? studentId,
        string? subject, int? page, int? pageSize, CancellationToken cancellationToken)
    {
        var currentPage = page ?? 1;
        var size = pageSize ?? 20;
        if (currentPage < 1 || currentPage > 1_000_000 || size < 1 || size > 100)
            return Results.ValidationProblem(new Dictionary<string, string[]>
            { ["pagination"] = ["page must be 1–1000000 and pageSize must be 1–100."] });

        var query = Filter(db, studentId, subject);
        var total = await query.CountAsync(cancellationToken);
        var rows = await query.OrderBy(row => row.Id)
            .Skip((currentPage - 1) * size).Take(size).ToListAsync(cancellationToken);
        return Results.Ok(new
        {
            items = rows.Select(ResultResponse.From),
            total,
            page = currentPage,
            pageSize = size
        });
    }

    private static async Task<IResult> Get(long id, ResultsDbContext db, CancellationToken cancellationToken)
    {
        var row = await db.Results.AsNoTracking().SingleOrDefaultAsync(row => row.Id == id, cancellationToken);
        return row is null ? Missing() : Results.Ok(ResultResponse.From(row));
    }

    private static async Task<IResult> Create(ResultRequest request, ResultsDbContext db,
        CancellationToken cancellationToken)
    {
        var errors = request.Validate();
        if (errors.Count > 0)
            return Results.ValidationProblem(errors);

        var row = new StudentResult
        {
            StudentId = "", Subject = "", SubjectKey = "", CreatedAtUtc = DateTime.UtcNow
        };
        request.ApplyTo(row);
        db.Results.Add(row);
        try
        {
            await db.SaveChangesAsync(cancellationToken);
        }
        catch (DbUpdateException exception) when (IsDuplicate(exception))
        {
            return Duplicate();
        }
        return Results.Created($"/api/results/{row.Id}", ResultResponse.From(row));
    }

    private static async Task<IResult> Update(long id, ResultRequest request, ResultsDbContext db,
        CancellationToken cancellationToken)
    {
        var errors = request.Validate();
        if (errors.Count > 0)
            return Results.ValidationProblem(errors);
        var row = await db.Results.SingleOrDefaultAsync(row => row.Id == id, cancellationToken);
        if (row is null)
            return Missing();

        request.ApplyTo(row);
        try
        {
            await db.SaveChangesAsync(cancellationToken);
        }
        catch (DbUpdateException exception) when (IsDuplicate(exception))
        {
            return Duplicate();
        }
        return Results.Ok(ResultResponse.From(row));
    }

    private static async Task<IResult> Delete(long id, ResultsDbContext db, CancellationToken cancellationToken)
    {
        var deleted = await db.Results.Where(row => row.Id == id).ExecuteDeleteAsync(cancellationToken);
        return deleted == 0 ? Missing() : Results.NoContent();
    }

    private static async Task<IResult> Summary(ResultsDbContext db, string? studentId,
        string? subject, CancellationToken cancellationToken)
    {
        // All metrics come from the same short read transaction, giving a consistent snapshot.
        await using var transaction = await db.Database.BeginTransactionAsync(cancellationToken);
        var query = Filter(db, studentId, subject);
        var count = await query.CountAsync(cancellationToken);
        var students = await query.Select(row => row.StudentId).Distinct().CountAsync(cancellationToken);
        var passed = await query.CountAsync(row => row.Score >= 50, cancellationToken);
        var average = await query.AverageAsync(row => (double?)row.Score, cancellationToken);
        var subjects = await query.GroupBy(row => row.SubjectKey).Select(group => new
        {
            subject = group.Min(row => row.Subject),
            resultCount = group.Count(),
            averageScore = Math.Round(group.Average(row => (double)row.Score), 2),
            passedResults = group.Count(row => row.Score >= 50)
        }).OrderBy(row => row.subject).ToListAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);
        return Results.Ok(new
        {
            totalResults = count,
            totalStudents = students,
            averageScore = average is null ? (double?)null : Math.Round(average.Value, 2),
            passedResults = passed,
            failedResults = count - passed,
            passRatePercent = count == 0 ? (double?)null : Math.Round(100d * passed / count, 2),
            passMark = 50,
            bySubject = subjects
        });
    }

    private static bool IsDuplicate(DbUpdateException exception) =>
        exception.InnerException is SqliteException { SqliteExtendedErrorCode: 2067 };

    private static IResult Missing() => Results.Problem(statusCode: 404, title: "Result not found");
    private static IResult Duplicate() => Results.Problem(statusCode: 409,
        title: "This student already has a result for this subject.");
}
