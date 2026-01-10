using System.Collections.Concurrent;

namespace JALM.Service;

public class SmartWatcher : IDisposable
{
    private readonly ConfigService _configService;
    private readonly DatabaseService _databaseService;
    private readonly DocumentService _documentService;
    private readonly AnalyticsService _analyticsService;
    private readonly ILogger<SmartWatcher> _logger;
    private FileSystemWatcher? _watcher;
    private readonly ConcurrentDictionary<string, CancellationTokenSource> _pendingEvents = new();
    private readonly int _debounceMs = 500;

    public SmartWatcher(ConfigService configService, DatabaseService databaseService, DocumentService documentService, AnalyticsService analyticsService, ILogger<SmartWatcher> logger)
    {
        _configService = configService;
        _databaseService = databaseService;
        _documentService = documentService;
        _analyticsService = analyticsService;
        _logger = logger;

        _configService.OnConfigChanged += Restart;
    }

    public void Start()
    {
        Stop();

        var root = _configService.ActiveRoot;
        if (string.IsNullOrEmpty(root) || !Directory.Exists(root))
        {
            _logger.LogWarning("Cannot start SmartWatcher: Active root '{Root}' does not exist.", root);
            return;
        }

        _logger.LogInformation("Starting SmartWatcher on {Root}", root);
        _watcher = new FileSystemWatcher(root)
        {
            IncludeSubdirectories = true,
            NotifyFilter = NotifyFilters.DirectoryName | NotifyFilters.CreationTime,
            EnableRaisingEvents = true
        };

        _watcher.Created += OnChanged;
        _watcher.Renamed += OnRenamed;
        _watcher.Deleted += OnDeleted;
    }

    public void Stop()
    {
        if (_watcher != null)
        {
            _watcher.EnableRaisingEvents = false;
            _watcher.Dispose();
            _watcher = null;
        }
        _logger.LogInformation("SmartWatcher stopped.");
    }

    private void Restart()
    {
        _logger.LogInformation("Config changed, restarting SmartWatcher...");
        Start();
    }

    private void OnChanged(object sender, FileSystemEventArgs e)
    {
        _logger.LogDebug("Watcher event: {Type} - {Path}", e.ChangeType, e.FullPath);
        if (!Directory.Exists(e.FullPath)) 
        {
            _logger.LogDebug("Ignore: Not a directory - {Path}", e.FullPath);
            return;
        }
        DebounceEvent(e.FullPath, () => ProcessUpsert(e.FullPath));
    }

    private void OnRenamed(object sender, RenamedEventArgs e)
    {
        _logger.LogDebug("Watcher event: {Type} - {OldPath} -> {NewPath}", e.ChangeType, e.OldFullPath, e.FullPath);
        // Handle deletion of old path record
        _databaseService.DeleteApplicationByPath(e.OldFullPath);

        if (!Directory.Exists(e.FullPath)) 
        {
            _logger.LogDebug("Ignore: Not a directory - {Path}", e.FullPath);
            return;
        }
        DebounceEvent(e.FullPath, () => ProcessUpsert(e.FullPath));
    }

    private void OnDeleted(object sender, FileSystemEventArgs e)
    {
        _logger.LogDebug("Watcher event: {Type} - {Path}", e.ChangeType, e.FullPath);
        _databaseService.DeleteApplicationByPath(e.FullPath);
        _analyticsService.RefreshAnalytics();
    }

    private void DebounceEvent(string path, Action action)
    {
        if (_pendingEvents.TryRemove(path, out var oldCts))
        {
            oldCts.Cancel();
            oldCts.Dispose();
        }

        var cts = new CancellationTokenSource();
        _pendingEvents[path] = cts;

        Task.Delay(_debounceMs, cts.Token).ContinueWith(t =>
        {
            if (t.IsCompletedSuccessfully)
            {
                action();
                _pendingEvents.TryRemove(path, out _);
            }
        });
    }

    private void ProcessUpsert(string fullPath)
    {
        try
        {
            var root = Path.GetFullPath(_configService.ActiveRoot!);
            var folder = Path.GetFullPath(fullPath);
            
            // Expected depth: Root / Company / Role
            // Relative path should look like "Company\Role"
            var relative = Path.GetRelativePath(root, folder);
            var parts = relative.Split(Path.DirectorySeparatorChar);

            if (parts.Length == 2)
            {
                string company = parts[0];
                string role = parts[1];
                DateTime created = Directory.GetCreationTime(fullPath);

                _logger.LogInformation("Processing folder: {Company} / {Role}", company, role);
                _databaseService.UpsertApplication(company, role, fullPath, created);

                // Phase 3: Generate documents
                _documentService.GenerateDocuments(company, role, fullPath);

                // Phase 4: Refresh Analytics
                _analyticsService.RefreshAnalytics();
            }
            else
            {
                _logger.LogDebug("Ignoring folder at depth {Depth}: {Path}", parts.Length, relative);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing folder upsert for {Path}", fullPath);
        }
    }

    public void Dispose()
    {
        Stop();
        foreach (var cts in _pendingEvents.Values)
        {
            cts.Cancel();
            cts.Dispose();
        }
    }
}
