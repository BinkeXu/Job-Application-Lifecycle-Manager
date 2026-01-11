using System.Text.Json;

namespace JALM.Service;

public class ConfigService
{
    private readonly string _configPath;
    private readonly ILogger<ConfigService> _logger;
    private FileSystemWatcher? _watcher;

    public string? ActiveRoot { get; private set; }
    public string? UserName { get; private set; }
    public string? CvTemplatePath { get; private set; }
    public string? CoverLetterTemplatePath { get; private set; }

    public event Action? OnConfigChanged;

    public ConfigService(ILogger<ConfigService> logger)
    {
        _logger = logger;
        
        // Search for config.json. 
        // We first check if the Python app has told us where the config is (via Environment Variable).
        // This is crucial when running as a bundled .exe!
        var currentDir = Environment.GetEnvironmentVariable("JALM_CONFIG_DIR") ?? AppDomain.CurrentDomain.BaseDirectory;
        
        _logger.LogInformation("Searching for config in: {Dir}", currentDir);

        while (!string.IsNullOrEmpty(currentDir))
        {
            var potentialPath = Path.Combine(currentDir, "config.json");
            if (File.Exists(potentialPath))
            {
                _configPath = potentialPath;
                _logger.LogInformation("Found config at: {Path}", _configPath);
                break;
            }
            
            // Move up one folder to see if it's there.
            var parent = Path.GetDirectoryName(currentDir);
            if (parent == currentDir) break; // Avoid infinite loop
            currentDir = parent;
        }

        if (string.IsNullOrEmpty(_configPath))
        {
            // Fallback to the same folder as the service file itself.
            _configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
        }

        LoadGlobalConfig();
        SetupWatcher();
    }

    private void LoadGlobalConfig()
    {
        try
        {
            if (File.Exists(_configPath))
            {
                var json = File.ReadAllText(_configPath);
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty("active_root", out var rootProp))
                {
                    ActiveRoot = rootProp.GetString();
                    _logger.LogInformation("Global configuration loaded. Active Root: {ActiveRoot}", ActiveRoot);
                    LoadWorkspaceConfig();
                }
            }
            else
            {
                _logger.LogWarning("Config file not found at {Path}", _configPath);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading global configuration");
        }
    }

    private void LoadWorkspaceConfig()
    {
        if (string.IsNullOrEmpty(ActiveRoot)) return;

        var workspaceConfigPath = Path.Combine(ActiveRoot, "jalm_config.json");
        try
        {
            if (File.Exists(workspaceConfigPath))
            {
                var json = File.ReadAllText(workspaceConfigPath);
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                UserName = root.GetProperty("user_name").GetString();
                CvTemplatePath = root.GetProperty("cv_template_path").GetString();
                CoverLetterTemplatePath = root.GetProperty("cover_letter_template_path").GetString();

                _logger.LogInformation("Workspace configuration loaded. User: {User}", UserName);
            }
            else
            {
                _logger.LogWarning("Workspace config (jalm_config.json) not found in {Root}", ActiveRoot);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading workspace configuration from {Path}", workspaceConfigPath);
        }
    }

    private void SetupWatcher()
    {
        var directory = Path.GetDirectoryName(_configPath);
        if (string.IsNullOrEmpty(directory) || !Directory.Exists(directory)) return;

        _watcher = new FileSystemWatcher(directory, Path.GetFileName(_configPath))
        {
            EnableRaisingEvents = true,
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName
        };

        _watcher.Changed += (s, e) => 
        {
            _logger.LogInformation("Config file change detected.");
            // Debounce or just reload
            Thread.Sleep(200); 
            LoadGlobalConfig();
            OnConfigChanged?.Invoke();
        };
    }
}
