using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using System.Text.RegularExpressions;

namespace JALM.Service;

// This service is your "Personal Assistant" that writes your documents.
// It copies your CV and Cover Letter templates and fills in the blanks.
public class DocumentService
{
    private readonly ConfigService _configService;
    private readonly ILogger<DocumentService> _logger;

    public DocumentService(ConfigService configService, ILogger<DocumentService> logger)
    {
        _configService = configService;
        _logger = logger;
    }

    // The main method to generate documents for a new application.
    public void GenerateDocuments(string company, string role, string targetFolder)
    {
        var userName = _configService.UserName ?? "User";
        var cvTemplate = _configService.CvTemplatePath;
        var clTemplate = _configService.CoverLetterTemplatePath;

        // If the user hasn't chosen templates yet, we can't do anything.
        if (string.IsNullOrEmpty(cvTemplate) || string.IsNullOrEmpty(clTemplate))
        {
            _logger.LogWarning("Template paths are not configured. Skipping document generation.");
            return;
        }

        // Clean up the role name so it's safe to use as a filename (removes weird characters).
        string roleClean = Regex.Replace(role, @"[^a-zA-Z0-9\s\-_]", "").Trim();

        // Create the new filenames, like: "Binke_CV_Software Engineer.docx"
        string cvDest = Path.Combine(targetFolder, $"{userName}_CV_{roleClean}{Path.GetExtension(cvTemplate)}");
        string clDest = Path.Combine(targetFolder, $"{userName}_Cover Letter_{roleClean}{Path.GetExtension(clTemplate)}");

        // 1. Copy the CV (no changes needed)
        TryCopyAndProcess(cvTemplate, cvDest, null);
        
        // 2. Copy the Cover Letter and update the date inside it!
        TryCopyAndProcess(clTemplate, clDest, ProcessCoverLetter);
    }

    // Helper that copies a file and optionally runs a "special process" on it.
    private void TryCopyAndProcess(string source, string dest, Action<string>? processAction)
    {
        if (!File.Exists(source))
        {
            _logger.LogWarning("Template file not found: {Path}", source);
            return;
        }

        // We try 3 times in case the file is locked (e.g., if Word is open).
        for (int i = 0; i < 3; i++)
        {
            try
            {
                // Only copy if the file doesn't already exist.
                if (!File.Exists(dest))
                {
                    File.Copy(source, dest, true);
                    _logger.LogInformation("Generated document: {Path}", Path.GetFileName(dest));
                }
                
                // If there's a special step (like date replacement), do it now.
                processAction?.Invoke(dest);
                return;
            }
            catch (IOException) when (i < 2)
            {
                // Wait 1 second before trying again.
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

    // This method opens the Word file and swaps "{Date}" with today's date.
    private void ProcessCoverLetter(string filePath)
    {
        try
        {
            // We use a library called OpenXML to "look inside" the Word file.
            using (WordprocessingDocument doc = WordprocessingDocument.Open(filePath, true))
            {
                var body = doc.MainDocumentPart?.Document.Body;
                if (body == null) return;

                // Create a pretty date, like "10, January 2026"
                string dateStr = DateTime.Now.ToString("d, MMMM yyyy");
                bool modified = false;

                // Search through all the text blocks in the document.
                foreach (var text in body.Descendants<Text>())
                {
                    // If we find the placeholder "{Date}", replace it!
                    if (text.Text.Contains("{Date}"))
                    {
                        text.Text = text.Text.Replace("{Date}", dateStr);
                        modified = true;
                    }
                }
                
                // Only save if we actually changed something.
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
