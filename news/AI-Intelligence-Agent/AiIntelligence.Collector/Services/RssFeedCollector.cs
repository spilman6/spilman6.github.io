using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using AiIntelligence.Core.Entities;
using AiIntelligence.Core.Intelligence;
using AiIntelligence.Infrastructure.Persistence;
using CodeHollow.FeedReader;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace AiIntelligence.Collector.Services;

public sealed partial class RssFeedCollector(
    ArticlesDbContext dbContext,
    ILogger<RssFeedCollector> logger) : IRssFeedCollector
{
    private const string UserAgent = "AiIntelligencePlatform/1.0";

    public async Task<RssImportResult> ImportAsync(
        IEnumerable<string> feedUrls,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(feedUrls);

        var imported = 0;
        var skipped = 0;
        var seenUrls = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var seenHashes = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var feedUrl in feedUrls.Where(url => !string.IsNullOrWhiteSpace(url)).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            cancellationToken.ThrowIfCancellationRequested();

            Feed feed;
            try
            {
                feed = await FeedReader.ReadAsync(feedUrl, cancellationToken, autoRedirect: true, userAgent: UserAgent);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                logger.LogWarning(ex, "RSS import skipped feed {FeedUrl} because it could not be read.", feedUrl);
                skipped++;
                continue;
            }

            var candidates = feed.Items
                .Select(item => CreateCandidate(feed, item))
                .Where(article => article is not null)
                .Cast<Article>()
                .ToList();

            if (candidates.Count == 0)
            {
                continue;
            }

            var urls = candidates.Select(article => article.Url).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
            var hashes = candidates.Select(article => article.Hash).Distinct(StringComparer.OrdinalIgnoreCase).ToList();

            var existingUrls = await dbContext.Articles
                .AsNoTracking()
                .Where(article => urls.Contains(article.Url))
                .Select(article => article.Url)
                .ToListAsync(cancellationToken);

            var existingHashes = await dbContext.Articles
                .AsNoTracking()
                .Where(article => hashes.Contains(article.Hash))
                .Select(article => article.Hash)
                .ToListAsync(cancellationToken);

            var existingUrlSet = existingUrls.ToHashSet(StringComparer.OrdinalIgnoreCase);
            var existingHashSet = existingHashes.ToHashSet(StringComparer.OrdinalIgnoreCase);

            foreach (var article in candidates)
            {
                if (existingUrlSet.Contains(article.Url)
                    || existingHashSet.Contains(article.Hash)
                    || !seenUrls.Add(article.Url)
                    || !seenHashes.Add(article.Hash))
                {
                    skipped++;
                    continue;
                }

                dbContext.Articles.Add(article);
                imported++;
            }
        }

        if (imported > 0)
        {
            await dbContext.SaveChangesAsync(cancellationToken);
        }

        return new RssImportResult(imported, skipped);
    }

    private static Article? CreateCandidate(Feed feed, FeedItem item)
    {
        var url = NormalizeUrl(item.Link);
        if (string.IsNullOrWhiteSpace(url))
        {
            return null;
        }

        var title = CleanText(item.Title);
        if (string.IsNullOrWhiteSpace(title))
        {
            title = url;
        }

        var summary = CleanText(item.Description);
        var content = string.IsNullOrWhiteSpace(item.Content) ? summary : item.Content.Trim();
        var publishedAt = item.PublishingDate.HasValue
            ? new DateTimeOffset(DateTime.SpecifyKind(item.PublishingDate.Value, DateTimeKind.Utc))
            : DateTimeOffset.UtcNow;

        var category = item.Categories?.FirstOrDefault();
        var source = CleanText(feed.Title);
        var hash = ComputeHash($"{url}|{title}|{publishedAt:O}|{summary}");

        return new Article
        {
            Title = title,
            Source = string.IsNullOrWhiteSpace(source) ? "Unknown" : source,
            Url = url,
            ImageUrl = string.IsNullOrWhiteSpace(feed.ImageUrl) ? null : feed.ImageUrl,
            PublishedAt = publishedAt,
            Summary = string.IsNullOrWhiteSpace(summary) ? null : summary,
            Content = string.IsNullOrWhiteSpace(content) ? null : content,
            Author = string.IsNullOrWhiteSpace(item.Author) ? null : item.Author.Trim(),
            Category = string.IsNullOrWhiteSpace(category) ? null : category.Trim(),
            Hash = hash,
            ImportanceScore = 0,
            ConfidenceScore = 0,
            CreatedAt = DateTimeOffset.UtcNow
        };
    }

    private static string? NormalizeUrl(string? url)
    {
        if (string.IsNullOrWhiteSpace(url))
        {
            return null;
        }

        return Uri.TryCreate(url.Trim(), UriKind.Absolute, out var uri)
            ? uri.GetLeftPart(UriPartial.Path).TrimEnd('/')
            : url.Trim();
    }

    private static string? CleanText(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }

        var withoutMarkup = HtmlTagRegex().Replace(value, " ");
        var decoded = WebUtility.HtmlDecode(withoutMarkup);

        return WhitespaceRegex().Replace(decoded, " ").Trim();
    }

    private static string ComputeHash(string value)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(value));
        return Convert.ToHexString(bytes);
    }

    [GeneratedRegex("<.*?>", RegexOptions.Compiled)]
    private static partial Regex HtmlTagRegex();

    [GeneratedRegex("\\s+", RegexOptions.Compiled)]
    private static partial Regex WhitespaceRegex();
}
