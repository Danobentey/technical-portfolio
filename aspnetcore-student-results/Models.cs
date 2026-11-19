using System.Text.RegularExpressions;

namespace StudentResults.Api;

public sealed class StudentResult
{
    public long Id { get; set; }
    public required string StudentId { get; set; }
    public required string Subject { get; set; }
    public required string SubjectKey { get; set; }
    public int Score { get; set; }
    public DateTime CreatedAtUtc { get; set; }
    public DateTime UpdatedAtUtc { get; set; }
}

public sealed record ResultRequest(string? StudentId, string? Subject, int? Score)
{
    public Dictionary<string, string[]> Validate()
    {
        var errors = new Dictionary<string, string[]>();
        if (StudentId is null || !Regex.IsMatch(StudentId.Trim(), @"\A[A-Za-z0-9][A-Za-z0-9_-]{0,31}\z"))
            errors["studentId"] = ["Use 1–32 letters, digits, underscores or hyphens; start with a letter or digit."];
        if (string.IsNullOrWhiteSpace(Subject) || Subject.Trim().Length > 80)
            errors["subject"] = ["Provide a subject containing 1–80 characters."];
        if (Score is null || Score < 0 || Score > 100)
            errors["score"] = ["Provide a whole-number score between 0 and 100."];
        return errors;
    }

    public void ApplyTo(StudentResult result)
    {
        result.StudentId = StudentId!.Trim().ToUpperInvariant();
        result.Subject = Subject!.Trim();
        result.SubjectKey = result.Subject.ToUpperInvariant();
        result.Score = Score!.Value;
        result.UpdatedAtUtc = DateTime.UtcNow;
    }
}

public sealed record ResultResponse(long Id, string StudentId, string Subject, int Score,
    bool Passed, DateTime CreatedAtUtc, DateTime UpdatedAtUtc)
{
    public static ResultResponse From(StudentResult result) => new(result.Id,
        result.StudentId, result.Subject, result.Score, result.Score >= 50,
        result.CreatedAtUtc, result.UpdatedAtUtc);
}
