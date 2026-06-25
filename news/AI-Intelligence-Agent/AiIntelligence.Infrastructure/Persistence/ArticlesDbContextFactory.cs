using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace AiIntelligence.Infrastructure.Persistence;

public sealed class ArticlesDbContextFactory : IDesignTimeDbContextFactory<ArticlesDbContext>
{
    public ArticlesDbContext CreateDbContext(string[] args)
    {
        var connectionString = Environment.GetEnvironmentVariable("AI_INTELLIGENCE_DB")
            ?? "Host=localhost;Port=5432;Database=ai_intelligence;Username=postgres;Password=postgres";

        var optionsBuilder = new DbContextOptionsBuilder<ArticlesDbContext>();
        optionsBuilder.UseNpgsql(connectionString, npgsqlOptions =>
            npgsqlOptions.MigrationsAssembly(typeof(ArticlesDbContext).Assembly.FullName));

        return new ArticlesDbContext(optionsBuilder.Options);
    }
}
