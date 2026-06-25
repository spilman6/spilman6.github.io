using AiIntelligence.Core.Entities;
using Microsoft.EntityFrameworkCore;

namespace AiIntelligence.Infrastructure.Persistence;

public sealed class ArticlesDbContext(DbContextOptions<ArticlesDbContext> options) : DbContext(options)
{
    public DbSet<Article> Articles => Set<Article>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Article>(entity =>
        {
            entity.ToTable("articles");

            entity.HasKey(article => article.Id);

            entity.Property(article => article.Id)
                .ValueGeneratedOnAdd();

            entity.Property(article => article.Title)
                .HasMaxLength(500)
                .IsRequired();

            entity.Property(article => article.Source)
                .HasMaxLength(250)
                .IsRequired();

            entity.Property(article => article.Url)
                .HasMaxLength(2048)
                .IsRequired();

            entity.Property(article => article.ImageUrl)
                .HasMaxLength(2048);

            entity.Property(article => article.Summary)
                .HasMaxLength(4000);

            entity.Property(article => article.Author)
                .HasMaxLength(250);

            entity.Property(article => article.Category)
                .HasMaxLength(150);

            entity.Property(article => article.Hash)
                .HasMaxLength(64)
                .IsRequired();

            entity.Property(article => article.ImportanceScore)
                .HasPrecision(5, 2);

            entity.Property(article => article.ConfidenceScore)
                .HasPrecision(5, 2);

            entity.Property(article => article.CreatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            entity.HasIndex(article => article.Url)
                .IsUnique();

            entity.HasIndex(article => article.Hash)
                .IsUnique();

            entity.HasIndex(article => article.PublishedAt);
            entity.HasIndex(article => article.Category);
        });
    }
}
