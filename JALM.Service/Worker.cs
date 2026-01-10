namespace JALM.Service;

public class Worker : BackgroundService
{
    private readonly ILogger<Worker> _logger;
    private readonly ConfigService _configService;
    private readonly DatabaseService _databaseService;
    private readonly SmartWatcher _smartWatcher;
    private readonly AnalyticsService _analyticsService;

    public Worker(ILogger<Worker> logger, ConfigService configService, DatabaseService databaseService, SmartWatcher smartWatcher, AnalyticsService analyticsService)
    {
        _logger = logger;
        _configService = configService;
        _databaseService = databaseService;
        _smartWatcher = smartWatcher;
        _analyticsService = analyticsService;

        _configService.OnConfigChanged += HandleConfigChanged;
    }

    private void HandleConfigChanged()
    {
        _logger.LogInformation("Configuration changed. Re-initializing services...");
        _databaseService.InitializeDatabase();
        _smartWatcher.Start();
        _analyticsService.RefreshAnalytics();
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("JALM.Service starting at: {time}", DateTimeOffset.Now);

        // Initial setup
        _databaseService.InitializeDatabase();
        _smartWatcher.Start();
        _analyticsService.RefreshAnalytics();

        while (!stoppingToken.IsCancellationRequested)
        {
            // Periodic analytics refresh (30 mins)
            await Task.Delay(TimeSpan.FromMinutes(30), stoppingToken);
            _analyticsService.RefreshAnalytics();
        }
    }
}
