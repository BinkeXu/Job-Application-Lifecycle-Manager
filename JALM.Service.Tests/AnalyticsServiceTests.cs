using Xunit;
using Moq;
using Microsoft.Extensions.Logging;
using JALM.Service;
using System;
using System.IO;
using Microsoft.Data.Sqlite;
using System.Text.Json;

namespace JALM.Service.Tests;

[Collection("Sequential")]
public class AnalyticsServiceTests : IDisposable
{
    private readonly string _tempDir;
    private readonly AnalyticsService _analyticsService;
    private readonly DatabaseService _dbService;
    private readonly ConfigService _configService;

    public AnalyticsServiceTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(_tempDir);

        var mockLogger = new Mock<ILogger<ConfigService>>();
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", _tempDir);
        
        File.WriteAllText(Path.Combine(_tempDir, "config.json"), $@"{{
            ""active_root"": ""{_tempDir.Replace("\\", "\\\\")}""
        }}");
        File.WriteAllText(Path.Combine(_tempDir, "jalm_config.json"), $@"{{
            ""user_name"": ""Test"",
            ""cv_template_path"": """",
            ""cover_letter_template_path"": """"
        }}");
        
        _configService = new ConfigService(mockLogger.Object);
        // Force ActiveRoot via Reflection to bypass OS path escaping anomalies
        var prop = typeof(ConfigService).GetProperty("ActiveRoot");
        prop.DeclaringType.GetProperty("ActiveRoot").SetValue(_configService, _tempDir, System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance, null, null, null);
        
        _dbService = new DatabaseService(_configService, new Mock<ILogger<DatabaseService>>().Object);
        _analyticsService = new AnalyticsService(_dbService, _configService, new Mock<ILogger<AnalyticsService>>().Object);

        // Setup DB Schema
        using (var conn = new SqliteConnection(_dbService.GetConnectionString()))
        {
            conn.Open();
            var cmd = conn.CreateCommand();
            cmd.CommandText = "CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, company_name TEXT, role_name TEXT, folder_path TEXT, created_at TEXT, status TEXT)";
            cmd.ExecuteNonQuery();
        }
    }

    [Fact]
    public void RefreshAnalytics_GeneratesJsonAndCsvFiles()
    {
        // Arrange
        using (var conn = new SqliteConnection(_dbService.GetConnectionString()))
        {
            conn.Open();
            var cmd = conn.CreateCommand();
            // Insert dummy records for stats
            cmd.CommandText = @"
                INSERT INTO applications (company_name, role_name, folder_path, created_at, status) VALUES ('Apple', 'Dev', '/a/b', '2026-01-01', 'Applied');
                INSERT INTO applications (company_name, role_name, folder_path, created_at, status) VALUES ('Google', 'Lead, UX', '/b/c', '2026-01-01', 'Offer');
            ";
            cmd.ExecuteNonQuery();
        }

        // Assert ActiveRoot
        Assert.Equal(_tempDir, _configService.ActiveRoot);

        // Act
        _analyticsService.RefreshAnalytics();

        // Assert JSON Output
        var jsonPath = Path.Combine(_tempDir, "analytics.json");
        Assert.True(File.Exists(jsonPath));
        var jsonStr = File.ReadAllText(jsonPath);
        using var doc = JsonDocument.Parse(jsonStr);
        Assert.Equal(2, doc.RootElement.GetProperty("TotalApplications").GetInt32());
        Assert.Equal(1, doc.RootElement.GetProperty("Offers").GetInt32());

        // Assert CSV Output
        var csvPath = Path.Combine(_tempDir, "applications_export.csv");
        Assert.True(File.Exists(csvPath));
        var lines = File.ReadAllLines(csvPath);
        Assert.Equal(3, lines.Length); // 1 header + 2 rows
        // Verify CSV escaping worked for the comma in role
        Assert.Contains("\"Lead, UX\"", lines[1] + lines[2]);
    }

    public void Dispose()
    {
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", null);
        SqliteConnection.ClearAllPools();
        try { Directory.Delete(_tempDir, true); } catch { }
    }
}
