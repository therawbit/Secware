using Secware;

IHost host = Host.CreateDefaultBuilder(args)
    .UseWindowsService(config => {
        
    })
    .ConfigureServices(services =>
    {
        services.AddHostedService<Worker>();
    })
    .Build();

host.Run();
