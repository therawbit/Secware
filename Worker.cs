namespace Secware;

public class Worker : BackgroundService
{
    private readonly ILogger<Worker> _logger;

    public Worker(ILogger<Worker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            _logger.LogInformation("Worker running at: {time}", DateTimeOffset.Now);
            string folderPath = "/home/sudru/Downloads/test";
            using (var watcher = new FileSystemWatcher(folderPath))
        {
            // Watch for changes to the folder and its subfolders
            watcher.IncludeSubdirectories = true;

            // Watch for changes in files
            watcher.NotifyFilter = NotifyFilters.FileName;

            // Subscribe to the Created event
            watcher.Created += OnFileCreated;

            // Start watching
            watcher.EnableRaisingEvents = true;

            while (!stoppingToken.IsCancellationRequested)
            {
                // Your worker logic goes here

                await Task.Delay(1000, stoppingToken); // Check every second
            }
        }
        }
    }
    private void OnFileCreated(object sender, FileSystemEventArgs e)
    {
        // Check if the created file has a .exe extension
        if (Path.GetExtension(e.Name).Equals(".exe", StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogInformation($"New .exe file detected: {e.Name}");
            // You can perform additional actions here
        }
    }
}
