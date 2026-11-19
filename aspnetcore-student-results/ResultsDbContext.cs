using Microsoft.EntityFrameworkCore;

namespace StudentResults.Api;

public sealed class ResultsDbContext(DbContextOptions<ResultsDbContext> options) : DbContext(options)
{
    public DbSet<StudentResult> Results => Set<StudentResult>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var result = modelBuilder.Entity<StudentResult>();
        result.HasKey(row => row.Id);
        // The database, rather than a read-before-write check, arbitrates duplicates.
        result.HasIndex(row => new { row.StudentId, row.SubjectKey }).IsUnique();
        result.Property(row => row.StudentId).HasMaxLength(32);
        result.Property(row => row.Subject).HasMaxLength(80);
        // SQLite does not preserve DateTime.Kind, so restore UTC when reading.
        result.Property(row => row.CreatedAtUtc).HasConversion(
            value => value, value => DateTime.SpecifyKind(value, DateTimeKind.Utc));
        result.Property(row => row.UpdatedAtUtc).HasConversion(
            value => value, value => DateTime.SpecifyKind(value, DateTimeKind.Utc));
        result.ToTable("Results", table =>
            table.HasCheckConstraint("CK_Results_Score", "Score >= 0 AND Score <= 100"));
    }
}
