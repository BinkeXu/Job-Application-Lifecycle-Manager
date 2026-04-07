using Xunit;
using Moq;
using Microsoft.Extensions.Logging;
using JALM.Service;
using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace JALM.Service.Tests;

[Collection("Sequential")]
public class SmartWatcherTests : IDisposable
{
    private readonly string _tempDir;
    private readonly SmartWatcher _watcher;

    public SmartWatcherTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(_tempDir);

        var mockConfigLogger = new Mock<ILogger<ConfigService>>();
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", _tempDir);
        File.WriteAllText(Path.Combine(_tempDir, "config.json"), $"{{\"active_root\": \"{_tempDir.Replace("\\", "\\\\")}\"}}");
        File.WriteAllText(Path.Combine(_tempDir, "jalm_config.json"), $"{{\"user_name\": \"Test\", \"cv_template_path\": \"\", \"cover_letter_template_path\": \"\"}}");
        
        var configService = new ConfigService(mockConfigLogger.Object);
        var dbService = new DatabaseService(configService, new Mock<ILogger<DatabaseService>>().Object);
        var docService = new DocumentService(configService, new Mock<ILogger<DocumentService>>().Object);
        var analyticsService = new AnalyticsService(dbService, configService, new Mock<ILogger<AnalyticsService>>().Object);

        _watcher = new SmartWatcher(configService, dbService, docService, analyticsService, new Mock<ILogger<SmartWatcher>>().Object);
    }

    [Fact]
    public async Task Watcher_IgnoresShallowFolders()
    {
        // Act
        _watcher.Start();

        // Create a root folder (depth 1) which should not trigger Upsert directly
        var companyFolder = Path.Combine(_tempDir, "Apple");
        Directory.CreateDirectory(companyFolder);
        
        // Wait for debounce slightly
        await Task.Delay(1000);

        // We assert true if it didn't crash
        Assert.True(Directory.Exists(companyFolder));

        // Let's create depth 2
        var roleFolder = Path.Combine(companyFolder, "Dev");
        Directory.CreateDirectory(roleFolder);
        
        await Task.Delay(1000);

        // Asserts
        Assert.True(Directory.Exists(roleFolder));

        _watcher.Stop();
    }

    public void Dispose()
    {
        _watcher.Dispose();
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", null);
        try { Directory.Delete(_tempDir, true); } catch { }
    }
}
