using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using System.Text.RegularExpressions;

namespace JALM.Service;

public class DocumentService
{
    private readonly ConfigService _configService;
    private readonly ILogger<DocumentService> _logger;

    public DocumentService(ConfigService configService, ILogger<DocumentService> logger)
    {
        _configService = configService;
        _logger = logger;
    }

    public void GenerateDocuments(string company, string role, string targetFolder)
    {
        var userName = _configService.UserName ?? "User";
        var cvTemplate = _configService.CvTemplatePath;
        var clTemplate = _configService.CoverLetterTemplatePath;

        if (string.IsNullOrEmpty(cvTemplate) || string.IsNullOrEmpty(clTemplate))
        {
            _logger.LogWarning("Template paths are not configured. Skipping document generation.");
            return;
        }

        // Match Python's sanitization: "".join(c for c in role if c.isalnum() or c in (' ', '_', '-')).strip()
        string roleClean = Regex.Replace(role, @"[^a-zA-Z0-9\s\-_]", "").Trim();

        string cvDest = Path.Combine(targetFolder, $"{userName}_CV_{roleClean}{Path.GetExtension(cvTemplate)}");
        string clDest = Path.Combine(targetFolder, $"{userName}_Cover Letter_{roleClean}{Path.GetExtension(clTemplate)}");

        TryCopyAndProcess(cvTemplate, cvDest, null);
        TryCopyAndProcess(clTemplate, clDest, ProcessCoverLetter);
    }

    private void TryCopyAndProcess(string source, string dest, Action<string>? processAction)
    {
        if (!File.Exists(source))
        {
            _logger.LogWarning("Template file not found: {Path}", source);
            return;
        }

        for (int i = 0; i < 3; i++)
        {
            try
            {
                if (!File.Exists(dest))
                {
                    File.Copy(source, dest, true);
                    _logger.LogInformation("Generated document: {Path}", Path.GetFileName(dest));
                }
                
                processAction?.Invoke(dest);
                return;
            }
            catch (IOException) when (i < 2)
            {
                _logger.LogWarning("File locked, retrying ({Attempt}/3): {Path}", i + 1, dest);
                Thread.Sleep(1000);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to generate document: {Path}", dest);
                return;
            }
        }
    }

    private void ProcessCoverLetter(string filePath)
    {
        try
        {
            using (WordprocessingDocument doc = WordprocessingDocument.Open(filePath, true))
            {
                var body = doc.MainDocumentPart?.Document.Body;
                if (body == null) return;

                // Format: 10, January 2026
                string dateStr = DateTime.Now.ToString("d, MMMM yyyy");
                bool modified = false;

                foreach (var text in body.Descendants<Text>())
                {
                    if (text.Text.Contains("{Date}"))
                    {
                        text.Text = text.Text.Replace("{Date}", dateStr);
                        modified = true;
                    }
                }
                
                if (modified)
                {
                    doc.MainDocumentPart!.Document.Save();
                    _logger.LogInformation("Updated date in cover letter: {Path}", Path.GetFileName(filePath));
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing cover letter date replacement for {Path}", filePath);
        }
    }
}
