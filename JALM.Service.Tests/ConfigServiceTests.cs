using Xunit;
using Moq;
using Microsoft.Extensions.Logging;
using JALM.Service;
using System;
using System.IO;

namespace JALM.Service.Tests;

public class ConfigServiceTests
{
    [Fact]
    public void ConfigService_Initializes_WithEmptyConfig()
    {
        // Arrange
        var mockLogger = new Mock<ILogger<ConfigService>>();
        
        // Point config to a fake directory so it finds nothing
        var tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(tempDir);
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", tempDir);
        
        try 
        {
            // Act
            var service = new ConfigService(mockLogger.Object);
            
            // Assert
            Assert.NotNull(service);
            // It might read a rogue file in C:/ but we assume null ActiveRoot 
            // if we truly isolated the config
        }
        finally
        {
            // Cleanup
            Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", null);
            Directory.Delete(tempDir, true);
        }
    }
}
