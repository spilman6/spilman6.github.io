using AiIntelligence.Collector.Services;
using AiIntelligence.Core.Intelligence;
using Microsoft.Extensions.DependencyInjection;

namespace AiIntelligence.Collector.DependencyInjection;

public static class CollectorServiceCollectionExtensions
{
    public static IServiceCollection AddCollector(this IServiceCollection services)
    {
        services.AddScoped<IRssFeedCollector, RssFeedCollector>();

        return services;
    }
}
