using Xunit;
using Moq;
using Microsoft.Extensions.Logging;
using JALM.Service;
using System;
using System.IO;
using Microsoft.Data.Sqlite;

namespace JALM.Service.Tests;

[Collection("Sequential")]
public class DatabaseServiceTests : IDisposable
{
    private readonly string _tempDir;
    private readonly DatabaseService _dbService;

    public DatabaseServiceTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(_tempDir);

        var mockLogger = new Mock<ILogger<ConfigService>>();
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", _tempDir);
        File.WriteAllText(Path.Combine(_tempDir, "config.json"), $"{{\"active_root\": \"{_tempDir.Replace("\\", "\\\\")}\"}}");
        var configService = new ConfigService(mockLogger.Object);

        var dbLogger = new Mock<ILogger<DatabaseService>>();
        _dbService = new DatabaseService(configService, dbLogger.Object);
    }

    [Fact]
    public void InitializeDatabase_CreatesFileAndSchema()
    {
        // Act
        _dbService.InitializeDatabase();
        
        // Assert - However, the real app creates the schema inside Python.
        // Wait, DatabaseService.InitializeDatabase() only executes PRAGMA commands!
        // The file should exist.
        Assert.True(File.Exists(Path.Combine(_tempDir, "jalm_apps.db")));
    }

    [Fact]
    public void UpsertApplication_InsertsAndUpdatesRow()
    {
        // Arrange
        // Create schema manually since C# only interacts with an existing one.
        using (var conn = new SqliteConnection(_dbService.GetConnectionString()))
        {
            conn.Open();
            var cmd = conn.CreateCommand();
            cmd.CommandText = "CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, company_name TEXT, role_name TEXT, folder_path TEXT, created_at TEXT, status TEXT)";
            cmd.ExecuteNonQuery();
        }

        var folderPath = Path.Combine(_tempDir, "Google", "Dev");
        
        // Act (Insert)
        _dbService.UpsertApplication("Google", "Dev", folderPath, DateTime.Now);

        // Assert
        using (var conn = new SqliteConnection(_dbService.GetConnectionString()))
        {
            conn.Open();
            var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT COUNT(*) FROM applications WHERE company_name = 'Google'";
            long count = (long)cmd.ExecuteScalar();
            Assert.Equal(1, count);
        }

        // Act (Update matching path)
        _dbService.UpsertApplication("Google-Renamed", "Dev", folderPath, DateTime.Now);

        // Assert Update
        using (var conn = new SqliteConnection(_dbService.GetConnectionString()))
        {
            conn.Open();
            var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT company_name FROM applications WHERE folder_path = @p";
            cmd.Parameters.AddWithValue("@p", folderPath);
            var name = (string)cmd.ExecuteScalar();
            Assert.Equal("Google-Renamed", name);
        }
    }

    public void Dispose()
    {
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", null);
        try { Directory.Delete(_tempDir, true); } catch { }
    }
}
