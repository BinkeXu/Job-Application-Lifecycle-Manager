using Microsoft.Data.Sqlite;
using System.Text.Json;
using System.Text;

namespace JALM.Service;

// This service is like a "Calculator" for your job applications.
// It looks at the database, counts things up, and saves the results so the UI can show them.
public class AnalyticsService
{
    private readonly DatabaseService _databaseService;
    private readonly ConfigService _configService;
    private readonly ILogger<AnalyticsService> _logger;

    // This is the "Constructor". It connects this service to other parts of the app 
    // (like the Database and Settings) so it can use them.
    public AnalyticsService(DatabaseService databaseService, ConfigService configService, ILogger<AnalyticsService> logger)
    {
        _databaseService = databaseService;
        _configService = configService;
        _logger = logger;
    }

    // This is the main button to "Refresh" all your stats.
    public void RefreshAnalytics()
    {
        try
        {
            // 1. Do the math
            var metrics = CalculateMetrics();
            
            // 2. Save a quick summary (JSON) for the Dashboard UI
            SaveAnalyticsJson(metrics);
            
            // 3. Create a detailed spreadsheet (CSV) for you to open in Excel
            ExportToCsv();
        }
        catch (Exception ex)
        {
            // If something goes wrong, we log the error so we can fix it later.
            _logger.LogError(ex, "Error refreshing analytics");
        }
    }

    // This part actually talks to the SQLite database to get your numbers.
    private object CalculateMetrics()
    {
        _logger.LogInformation("Calculating analytics metrics...");
        
        using var connection = new SqliteConnection(_databaseService.GetConnectionString());
        connection.Open();

        // 1. Count Total Applications
        var totalCmd = connection.CreateCommand();
        totalCmd.CommandText = "SELECT COUNT(*) FROM applications";
        long total = (long)(totalCmd.ExecuteScalar() ?? 0L);

        // 2. Count Active Interviews
        var interviewCmd = connection.CreateCommand();
        interviewCmd.CommandText = "SELECT COUNT(*) FROM applications WHERE status = 'Interviewing'";
        long interviewing = (long)(interviewCmd.ExecuteScalar() ?? 0L);

        // 3. Count "Ghosted" Applications
        // We define 'Ghosted' as any job you applied to more than 30 days ago 
        // that hasn't moved past the 'Applied' status.
        var ghostedCmd = connection.CreateCommand();
        ghostedCmd.CommandText = @"
            SELECT COUNT(*) FROM applications 
            WHERE status = 'Applied' 
            AND datetime(created_at) < datetime('now', '-30 days')";
        long ghosted = (long)(ghostedCmd.ExecuteScalar() ?? 0L);

        // 4. Count Offers received
        var successCmd = connection.CreateCommand();
        successCmd.CommandText = "SELECT COUNT(*) FROM applications WHERE status = 'Offer'";
        long offers = (long)(successCmd.ExecuteScalar() ?? 0L);

        // We package all these numbers into a single object to be used later.
        return new
        {
            TotalApplications = total,
            Interviewing = interviewing,
            Ghosted = ghosted,
            Offers = offers,
            LastUpdated = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
        };
    }

    // Saves the numbers to a file called "analytics.json" in your job folder.
    private void SaveAnalyticsJson(object metrics)
    {
        if (string.IsNullOrEmpty(_configService.ActiveRoot)) return;

        var path = Path.Combine(_configService.ActiveRoot, "analytics.json");
        // Convert the 'metrics' object into a text format (JSON) that apps can easily read.
        var json = JsonSerializer.Serialize(metrics, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(path, json);
        _logger.LogInformation("Analytics saved to {Path}", path);
    }

    // Exports all your application data into a .CSV file (ready for Excel).
    private void ExportToCsv()
    {
        if (string.IsNullOrEmpty(_configService.ActiveRoot)) return;

        var path = Path.Combine(_configService.ActiveRoot, "applications_export.csv");
        _logger.LogInformation("Exporting data to CSV: {Path}", path);

        using var connection = new SqliteConnection(_databaseService.GetConnectionString());
        connection.Open();

        var cmd = connection.CreateCommand();
        // Get the latest applications first
        cmd.CommandText = "SELECT company_name, role_name, status, created_at, folder_path FROM applications ORDER BY created_at DESC";

        using var reader = cmd.ExecuteReader();
        var sb = new StringBuilder();
        // Add the header row for the spreadsheet
        sb.AppendLine("Company,Role,Status,Date Applied,Path");

        while (reader.Read())
        {
            // EscapeCsv makes sure that if a company name has a comma in it, 
            // it doesn't break the CSV file structure.
            var company = EscapeCsv(reader.GetString(0));
            var role = EscapeCsv(reader.GetString(1));
            var status = EscapeCsv(reader.GetString(2));
            var date = EscapeCsv(reader.GetString(3));
            var folderPath = EscapeCsv(reader.GetString(4));

            sb.AppendLine($"{company},{role},{status},{date},{folderPath}");
        }

        // Save the whole string as a UTF-8 text file.
        File.WriteAllText(path, sb.ToString(), Encoding.UTF8);
    }

    // This helper method wraps text in "quotes" if it contains commas.
    // This is vital for CSV files to open correctly in Excel!
    private string EscapeCsv(string val)
    {
        if (val.Contains(",") || val.Contains("\"") || val.Contains("\n"))
        {
            return $"\"{val.Replace("\"", "\"\"")}\"";
        }
        return val;
    }
}
