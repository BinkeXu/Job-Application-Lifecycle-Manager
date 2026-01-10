using JALM.Service;

var builder = Host.CreateApplicationBuilder(args);

// Register Services
builder.Services.AddSingleton<ConfigService>();
builder.Services.AddSingleton<DatabaseService>();
builder.Services.AddSingleton<DocumentService>();
builder.Services.AddSingleton<AnalyticsService>();
builder.Services.AddSingleton<SmartWatcher>();
builder.Services.AddHostedService<Worker>();

var host = builder.Build();
host.Run();
