using System.Collections.Concurrent;

namespace JALM.Service;

// This is the "Security Guard" of your folders. 
// It constantly watches your job application folder for any changes.
public class SmartWatcher : IDisposable
{
    private readonly ConfigService _configService;
    private readonly DatabaseService _databaseService;
    private readonly DocumentService _documentService;
    private readonly AnalyticsService _analyticsService;
    private readonly ILogger<SmartWatcher> _logger;
    private FileSystemWatcher? _watcher;

    // We use a dictionary to keep track of "Pending" changes.
    // This helps us avoid doing double work if you rename a folder multiple times quickly.
    private readonly ConcurrentDictionary<string, CancellationTokenSource> _pendingEvents = new();
    
    // 500ms delay to make sure Windows has finished creating/moving the folder.
    private readonly int _debounceMs = 500;

    public SmartWatcher(ConfigService configService, DatabaseService databaseService, DocumentService documentService, AnalyticsService analyticsService, ILogger<SmartWatcher> logger)
    {
        _configService = configService;
        _databaseService = databaseService;
        _documentService = documentService;
        _analyticsService = analyticsService;
        _logger = logger;

        // If you change your Root folder in the Python app, we automatically restart the watcher here.
        _configService.OnConfigChanged += Restart;
    }

    // Sets up the folder watcher and starts listening for events.
    public void Start()
    {
        Stop(); // Stop any old watcher first

        var root = _configService.ActiveRoot;
        if (string.IsNullOrEmpty(root) || !Directory.Exists(root))
        {
            _logger.LogWarning("Cannot start SmartWatcher: Active root '{Root}' does not exist.", root);
            return;
        }

        _logger.LogInformation("Starting SmartWatcher on {Root}", root);
        _watcher = new FileSystemWatcher(root)
        {
            IncludeSubdirectories = true, // Watch everything inside the main folder
            NotifyFilter = NotifyFilters.DirectoryName | NotifyFilters.CreationTime,
            EnableRaisingEvents = true
        };

        // Link the events (Create, Rename, Delete) to our methods below.
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

    // Triggered when a new folder is created.
    private void OnChanged(object sender, FileSystemEventArgs e)
    {
        _logger.LogDebug("Watcher event: {Type} - {Path}", e.ChangeType, e.FullPath);
        if (!Directory.Exists(e.FullPath)) 
        {
            return;
        }
        // Instead of processing immediately, we "Debounce" it (wait 500ms).
        DebounceEvent(e.FullPath, () => ProcessUpsert(e.FullPath));
    }

    // Triggered when you rename a folder (e.g., from 'New folder' to 'Google').
    private void OnRenamed(object sender, RenamedEventArgs e)
    {
        _logger.LogDebug("Watcher event: {Type} - {OldPath} -> {NewPath}", e.ChangeType, e.OldFullPath, e.FullPath);
        
        // Remove the old name from the database.
        _databaseService.DeleteApplicationByPath(e.OldFullPath);

        if (!Directory.Exists(e.FullPath)) 
        {
            return;
        }
        // Process the new name.
        DebounceEvent(e.FullPath, () => ProcessUpsert(e.FullPath));
    }

    // Triggered when you delete a folder.
    private void OnDeleted(object sender, FileSystemEventArgs e)
    {
        _logger.LogDebug("Watcher event: {Type} - {Path}", e.ChangeType, e.FullPath);
        _databaseService.DeleteApplicationByPath(e.FullPath);
        _analyticsService.RefreshAnalytics(); // Refresh stats since an app is gone.
    }

    // This is a "Timer" that waits 500ms before doing something.
    // If a new change happens for the SAME folder during that time, we reset the timer.
    // This is super important because Windows often fires multiple events for one action.
    private void DebounceEvent(string path, Action action)
    {
        if (_pendingEvents.TryRemove(path, out var oldCts))
        {
            oldCts.Cancel(); // Stop the previous timer
            oldCts.Dispose();
        }

        var cts = new CancellationTokenSource();
        _pendingEvents[path] = cts;

        Task.Delay(_debounceMs, cts.Token).ContinueWith(t =>
        {
            // Only run the action if the timer finished without being cancelled.
            if (t.IsCompletedSuccessfully)
            {
                action();
                _pendingEvents.TryRemove(path, out _);
            }
        });
    }

    // This part actually updates the database and generates your documents.
    private void ProcessUpsert(string fullPath)
    {
        try
        {
            var root = Path.GetFullPath(_configService.ActiveRoot!);
            var folder = Path.GetFullPath(fullPath);
            
            // We want to find folders like: Root / Company / Role
            var relative = Path.GetRelativePath(root, folder);
            var parts = relative.Split(Path.DirectorySeparatorChar);

            // parts.Length == 2 means it's a "Company\Role" folder.
            if (parts.Length == 2)
            {
                string company = parts[0];
                string role = parts[1];
                DateTime created = Directory.GetCreationTime(fullPath);

                _logger.LogInformation("Processing folder: {Company} / {Role}", company, role);
                
                // 1. Add/Update the application in the database.
                _databaseService.UpsertApplication(company, role, fullPath, created);

                // 2. Automatically create your CV and Cover Letter templates in that folder!
                _documentService.GenerateDocuments(company, role, fullPath);

                // 3. Update the global analytics numbers.
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
