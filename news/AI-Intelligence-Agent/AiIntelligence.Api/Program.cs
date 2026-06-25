using AiIntelligence.Collector.DependencyInjection;
using AiIntelligence.Core.Intelligence;
using AiIntelligence.Infrastructure.DependencyInjection;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddInfrastructure(builder.Configuration);
builder.Services.AddCollector();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.MapHealthChecks("/health");

app.MapPost("/api/intelligence/import-rss", async (
    ImportRssRequest request,
    IRssFeedCollector collector,
    CancellationToken cancellationToken) =>
{
    if (request.FeedUrls is null || request.FeedUrls.Length == 0)
    {
        return Results.BadRequest(new { error = "At least one RSS feed URL is required." });
    }

    var result = await collector.ImportAsync(request.FeedUrls, cancellationToken);

    return Results.Ok(result);
})
.WithName("ImportRss")
.WithSummary("Imports intelligence articles from RSS feeds.")
.WithDescription("Imports RSS articles into PostgreSQL while skipping duplicates by URL and SHA-256 hash.")
.Produces<RssImportResult>()
.Produces(StatusCodes.Status400BadRequest);

app.Run();

public sealed record ImportRssRequest(string[] FeedUrls);
