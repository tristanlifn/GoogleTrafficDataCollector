using System.Text;
using System.Text.Json;

namespace GoogleTrafficDataCollector;

public class RoutesResponse
{
    public List<Route> Routes { get; set; }
}

class Program
{
    static void Main(string[] args)
    {
        new Program();
    }
    
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    private readonly HttpClient HttpClient = new();
    private const string Url = "https://routes.googleapis.com/directions/v2:computeRoutes";
    private static string _routesFolderLocation = "";
    private static string _key = "";
    private static string _destinationAddress = "";
    private static string _originAddress = "";

    private Program()
    {
        if (!LoadConfig())
        {
            Console.WriteLine("No valid config file found in execution directory.");
            return;
        }
        
        try
        {
            string fileLocation = GetRelevantFileLocation();
            
            RoutesResponse result = ComputeRoutesAsync().Result;
            
            if (!result.Routes.Any())
                return;
            
            if (!File.Exists(fileLocation))
                File.Create(fileLocation).Close();
            
            string oldJson = File.ReadAllText(fileLocation);

            List<Route> oldRoutsList = [];
            if (!string.IsNullOrWhiteSpace(oldJson))
                oldRoutsList = JsonSerializer.Deserialize<RoutesResponse>(oldJson, JsonOptions)?.Routes ?? [];
            
            result.Routes?.AddRange(oldRoutsList);
            
            File.WriteAllText(fileLocation, JsonSerializer.Serialize(result, JsonOptions));
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Error: {ex.StatusCode} - {ex.Message}");
        }
    }

    private bool LoadConfig()
    {
        string appDir = AppContext.BaseDirectory;
        string configLocation = Path.Combine(appDir, "config.json");
        
        string configString = File.ReadAllText(configLocation);
        Config config = JsonSerializer.Deserialize<Config>(configString, JsonOptions) ?? new Config();
        
        if (string.IsNullOrEmpty(config.GoogleApiKey) || string.IsNullOrEmpty(config.OriginAddress) || string.IsNullOrEmpty(config.DestinationAddress) ||  string.IsNullOrEmpty(config.RoutesFolderLocation))
            return false;
        
        _key = config.GoogleApiKey;
        _routesFolderLocation =  config.RoutesFolderLocation;
        _originAddress = config.OriginAddress;
        _destinationAddress = config.DestinationAddress;
        
        return true;
    }

    private string GetRelevantFileLocation()
    {
        string fileLocation = $"{_routesFolderLocation}routes-{DateTime.Now:yyyy-MM-dd}.json";
            
        if (!Directory.Exists(_routesFolderLocation))
        {
            Directory.CreateDirectory(_routesFolderLocation);
            File.Create(fileLocation).Close();
        }
        else if (!Directory.EnumerateFiles(_routesFolderLocation).Any())
        {
            File.Create(fileLocation).Close();
        }
        else
        {
            DirectoryInfo directoryInfo = new(_routesFolderLocation);
            FileInfo myFile = directoryInfo.GetFiles()
                .OrderByDescending(f => f.CreationTime)
                .First();
                
            if (myFile.CreationTime.ToShortDateString() != DateTime.Now.ToShortDateString())
                fileLocation = myFile.FullName;
        }
        
        return fileLocation;
    }
    
    private async Task<RoutesResponse> ComputeRoutesAsync()
    {
        string json = "";
        
        string requestBody = $$"""
            {
                "computeAlternativeRoutes": false,
                "destination": {
                    "address": "{{_destinationAddress}}"
                },
                "origin": {
                    "address": "{{_originAddress}}"
                },
                "polylineQuality": "overview",
                "routeModifiers": {
                    "avoidTolls": false,
                    "avoidHighways": false,
                    "avoidFerries": false,
                    "avoidIndoor": false
                },
                "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
                "travelMode": "DRIVE",
                "languageCode": "en-US",
                "units": "METRIC"
            }
            """;
        
        try
        {
            using HttpRequestMessage request = new(HttpMethod.Post, Url);
            request.Content = new StringContent(requestBody, Encoding.UTF8, "application/json");
            request.Headers.Add("X-Goog-Api-Key", _key);
            request.Headers.Add("X-Goog-FieldMask",
                "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline");

            using HttpResponseMessage response = await HttpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            json = await response.Content.ReadAsStringAsync();
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
        
        return JsonSerializer.Deserialize<RoutesResponse>(json, JsonOptions) ?? new RoutesResponse();
    }
}