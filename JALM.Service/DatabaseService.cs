using Microsoft.Data.Sqlite;

namespace JALM.Service;

public class DatabaseService
{
    private readonly ConfigService _configService;
    private readonly ILogger<DatabaseService> _logger;

    public DatabaseService(ConfigService configService, ILogger<DatabaseService> logger)
    {
        _configService = configService;
        _logger = logger;
    }

    public string GetConnectionString()
    {
        var dbPath = "jalm_apps.db";
        if (!string.IsNullOrEmpty(_configService.ActiveRoot))
        {
            dbPath = Path.Combine(_configService.ActiveRoot, "jalm_apps.db");
        }
        
        return $"Data Source={dbPath};Mode=ReadWriteCreate;Cache=Shared;Pooling=True;";
    }

    public void InitializeDatabase()
    {
        try
        {
            using var connection = new SqliteConnection(GetConnectionString());
            connection.Open();

            using var command = connection.CreateCommand();
            command.CommandText = @"
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA busy_timeout=5000;
            ";
            command.ExecuteNonQuery();

            _logger.LogInformation("Database initialized with WAL mode.");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to initialize database");
        }
    }

    public void UpsertApplication(string company, string role, string path, DateTime createdAt)
    {
        try
        {
            using var connection = new SqliteConnection(GetConnectionString());
            connection.Open();

            // Check if application exists by company/role OR folder_path
            using var checkCmd = connection.CreateCommand();
            checkCmd.CommandText = "SELECT id FROM applications WHERE (company_name = @company AND role_name = @role) OR folder_path = @path";
            checkCmd.Parameters.AddWithValue("@company", company);
            checkCmd.Parameters.AddWithValue("@role", role);
            checkCmd.Parameters.AddWithValue("@path", path);
            var existingId = checkCmd.ExecuteScalar();

            using var command = connection.CreateCommand();
            if (existingId == null)
            {
                command.CommandText = @"
                    INSERT INTO applications (company_name, role_name, folder_path, created_at, status)
                    VALUES (@company, @role, @path, @createdAt, 'Applied')
                ";
            }
            else
            {
                command.CommandText = @"
                    UPDATE applications SET 
                        company_name = @company,
                        role_name = @role,
                        folder_path = @path,
                        created_at = @createdAt
                    WHERE id = @id
                ";
                command.Parameters.AddWithValue("@id", existingId);
            }

            command.Parameters.AddWithValue("@company", company);
            command.Parameters.AddWithValue("@role", role);
            command.Parameters.AddWithValue("@path", path);
            command.Parameters.AddWithValue("@createdAt", createdAt.ToString("yyyy-MM-dd HH:mm:ss"));
            
            command.ExecuteNonQuery();
            _logger.LogInformation("Synced application: {Company} - {Role}", company, role);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error upserting application for path {Path}", path);
        }
    }

    public void DeleteApplicationByPath(string path)
    {
        try
        {
            using var connection = new SqliteConnection(GetConnectionString());
            connection.Open();

            using var command = connection.CreateCommand();
            command.CommandText = "DELETE FROM applications WHERE folder_path = @path";
            command.Parameters.AddWithValue("@path", path);
            
            int rows = command.ExecuteNonQuery();
            if (rows > 0)
            {
                _logger.LogInformation("Deleted application record for path: {Path}", path);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting application for path {Path}", path);
        }
    }
}
