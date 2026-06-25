namespace AiIntelligence.Core.Entities;

public sealed class Article
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public required string Title { get; set; }

    public required string Source { get; set; }

    public required string Url { get; set; }

    public string? ImageUrl { get; set; }

    public DateTimeOffset PublishedAt { get; set; }

    public string? Summary { get; set; }

    public string? Content { get; set; }

    public string? Author { get; set; }

    public string? Category { get; set; }

    public required string Hash { get; set; }

    public decimal ImportanceScore { get; set; }

    public decimal ConfidenceScore { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}
