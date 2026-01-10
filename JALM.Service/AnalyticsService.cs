using Microsoft.Data.Sqlite;
using System.Text.Json;
using System.Text;

namespace JALM.Service;

public class AnalyticsService
{
    private readonly DatabaseService _databaseService;
    private readonly ConfigService _configService;
    private readonly ILogger<AnalyticsService> _logger;

    public AnalyticsService(DatabaseService databaseService, ConfigService configService, ILogger<AnalyticsService> logger)
    {
        _databaseService = databaseService;
        _configService = configService;
        _logger = logger;
    }

    public void RefreshAnalytics()
    {
        try
        {
            var metrics = CalculateMetrics();
            SaveAnalyticsJson(metrics);
            ExportToCsv();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error refreshing analytics");
        }
    }

    private object CalculateMetrics()
    {
        _logger.LogInformation("Calculating analytics metrics...");
        
        using var connection = new SqliteConnection(_databaseService.GetConnectionString());
        connection.Open();

        // 1. Total Applications
        var totalCmd = connection.CreateCommand();
        totalCmd.CommandText = "SELECT COUNT(*) FROM applications";
        long total = (long)(totalCmd.ExecuteScalar() ?? 0L);

        // 2. Interviewing
        var interviewCmd = connection.CreateCommand();
        interviewCmd.CommandText = "SELECT COUNT(*) FROM applications WHERE status = 'Interviewing'";
        long interviewing = (long)(interviewCmd.ExecuteScalar() ?? 0L);

        // 3. Ghosted (No activity for 30 days)
        var ghostedCmd = connection.CreateCommand();
        ghostedCmd.CommandText = @"
            SELECT COUNT(*) FROM applications 
            WHERE status = 'Applied' 
            AND datetime(created_at) < datetime('now', '-30 days')";
        long ghosted = (long)(ghostedCmd.ExecuteScalar() ?? 0L);

        // 4. Success Rate
        var successCmd = connection.CreateCommand();
        successCmd.CommandText = "SELECT COUNT(*) FROM applications WHERE status = 'Offer'";
        long offers = (long)(successCmd.ExecuteScalar() ?? 0L);

        return new
        {
            TotalApplications = total,
            Interviewing = interviewing,
            Ghosted = ghosted,
            Offers = offers,
            LastUpdated = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
        };
    }

    private void SaveAnalyticsJson(object metrics)
    {
        if (string.IsNullOrEmpty(_configService.ActiveRoot)) return;

        var path = Path.Combine(_configService.ActiveRoot, "analytics.json");
        var json = JsonSerializer.Serialize(metrics, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(path, json);
        _logger.LogInformation("Analytics saved to {Path}", path);
    }

    private void ExportToCsv()
    {
        if (string.IsNullOrEmpty(_configService.ActiveRoot)) return;

        var path = Path.Combine(_configService.ActiveRoot, "applications_export.csv");
        _logger.LogInformation("Exporting data to CSV: {Path}", path);

        using var connection = new SqliteConnection(_databaseService.GetConnectionString());
        connection.Open();

        var cmd = connection.CreateCommand();
        cmd.CommandText = "SELECT company_name, role_name, status, created_at, folder_path FROM applications ORDER BY created_at DESC";

        using var reader = cmd.ExecuteReader();
        var sb = new StringBuilder();
        sb.AppendLine("Company,Role,Status,Date Applied,Path");

        while (reader.Read())
        {
            var company = EscapeCsv(reader.GetString(0));
            var role = EscapeCsv(reader.GetString(1));
            var status = EscapeCsv(reader.GetString(2));
            var date = EscapeCsv(reader.GetString(3));
            var folderPath = EscapeCsv(reader.GetString(4));

            sb.AppendLine($"{company},{role},{status},{date},{folderPath}");
        }

        File.WriteAllText(path, sb.ToString(), Encoding.UTF8);
    }

    private string EscapeCsv(string val)
    {
        if (val.Contains(",") || val.Contains("\"") || val.Contains("\n"))
        {
            return $"\"{val.Replace("\"", "\"\"")}\"";
        }
        return val;
    }
}
