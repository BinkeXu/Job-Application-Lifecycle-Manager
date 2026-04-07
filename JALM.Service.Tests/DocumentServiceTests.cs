using Xunit;
using Moq;
using Microsoft.Extensions.Logging;
using JALM.Service;
using System;
using System.IO;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace JALM.Service.Tests;

[Collection("Sequential")]
public class DocumentServiceTests : IDisposable
{
    private readonly string _tempDir;
    private readonly DocumentService _docService;

    public DocumentServiceTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(_tempDir);

        var mockLogger = new Mock<ILogger<ConfigService>>();
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", _tempDir);
        
        var cvPath = Path.Combine(_tempDir, "template_cv.docx");
        var clPath = Path.Combine(_tempDir, "template_cl.docx");

        // Create dummy valid DOCX for CL to test the replacement
        CreateDummyDocx(cvPath, "CV content");
        CreateDummyDocx(clPath, "To whom it may concern, on {Date}");

        File.WriteAllText(Path.Combine(_tempDir, "config.json"), $@"{{
            ""active_root"": ""{_tempDir.Replace("\\", "\\\\")}""
        }}");

        File.WriteAllText(Path.Combine(_tempDir, "jalm_config.json"), $@"{{
            ""user_name"": ""Tester"",
            ""cv_template_path"": ""{cvPath.Replace("\\", "\\\\")}"",
            ""cover_letter_template_path"": ""{clPath.Replace("\\", "\\\\")}""
        }}");

        var configService = new ConfigService(mockLogger.Object);
        _docService = new DocumentService(configService, new Mock<ILogger<DocumentService>>().Object);
    }

    private void CreateDummyDocx(string path, string text)
    {
        using (WordprocessingDocument wordDocument = WordprocessingDocument.Create(path, WordprocessingDocumentType.Document))
        {
            MainDocumentPart mainPart = wordDocument.AddMainDocumentPart();
            mainPart.Document = new Document(new Body(new Paragraph(new Run(new Text(text)))));
        }
    }

    [Fact]
    public void GenerateDocuments_CopiesCVAndModifiesCL()
    {
        // Arrange
        var targetFolder = Path.Combine(_tempDir, "output");
        Directory.CreateDirectory(targetFolder);

        // Act
        _docService.GenerateDocuments("Google", "Dev, Env", targetFolder);

        // Assert - Escapes the comma
        var expectedCV = Path.Combine(targetFolder, "Tester_CV_Dev Env.docx");
        var expectedCL = Path.Combine(targetFolder, "Tester_Cover Letter_Dev Env.docx");

        Assert.True(File.Exists(expectedCV));
        Assert.True(File.Exists(expectedCL));

        // Read CL and verify {Date} replaced
        using (WordprocessingDocument doc = WordprocessingDocument.Open(expectedCL, false))
        {
            var bodyText = doc.MainDocumentPart.Document.Body.InnerText;
            Assert.DoesNotContain("{Date}", bodyText);
            // Must contain a year
            Assert.Contains(DateTime.Now.Year.ToString(), bodyText);
        }
    }

    public void Dispose()
    {
        Environment.SetEnvironmentVariable("JALM_CONFIG_DIR", null);
        try { Directory.Delete(_tempDir, true); } catch { }
    }
}
