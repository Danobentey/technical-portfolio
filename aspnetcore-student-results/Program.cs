using Microsoft.EntityFrameworkCore;
using StudentResults.Api;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddProblemDetails();
builder.Services.ConfigureHttpJsonOptions(options =>
    options.SerializerOptions.NumberHandling = JsonNumberHandling.Strict);

var dataDirectory = Path.Combine(builder.Environment.ContentRootPath, "data");
Directory.CreateDirectory(dataDirectory);
var connection = builder.Configuration.GetConnectionString("Results")
    ?? $"Data Source={Path.Combine(dataDirectory, "student-results.db")};Default Timeout=10";
builder.Services.AddDbContext<ResultsDbContext>(options => options.UseSqlite(connection));

var app = builder.Build();
app.UseExceptionHandler();
app.UseDefaultFiles();
app.UseStaticFiles();

using (var scope = app.Services.CreateScope())
{
    // EnsureCreated is enough for this single-schema learning project.
    // Use migrations when the schema needs to evolve.
    var database = scope.ServiceProvider.GetRequiredService<ResultsDbContext>();
    database.Database.EnsureCreated();
}

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapResultsEndpoints();
app.Run();
