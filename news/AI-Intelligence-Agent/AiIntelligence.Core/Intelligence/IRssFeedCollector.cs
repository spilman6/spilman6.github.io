namespace AiIntelligence.Core.Intelligence;

public interface IRssFeedCollector
{
    Task<RssImportResult> ImportAsync(IEnumerable<string> feedUrls, CancellationToken cancellationToken = default);
}
