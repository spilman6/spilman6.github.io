using AiIntelligence.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace AiIntelligence.Infrastructure.DependencyInjection;

public static class InfrastructureServiceCollectionExtensions
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString("Articles")
            ?? throw new InvalidOperationException("Connection string 'Articles' is required.");

        services.AddDbContext<ArticlesDbContext>(options =>
            options.UseNpgsql(connectionString, npgsqlOptions =>
                npgsqlOptions.MigrationsAssembly(typeof(ArticlesDbContext).Assembly.FullName)));

        services.AddHealthChecks()
            .AddDbContextCheck<ArticlesDbContext>("postgresql");

        return services;
    }
}
