using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.VisualBasic;

namespace  HeadlessBrowserTest;

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
    private static string _key = "";
    private static string _destinationAddress = "";
    private static string _originAddress = "";

    private string _requestBody = $$"""
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

    private Program()
    {
        if (!LoadConfig())
        {
            Console.WriteLine("No valid config file found in execution directory.");
            return;
        }
        
        string documents = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
        string fileName = $"{documents}/routes.json";

        try
        {
            if (!File.Exists(fileName))
                File.Create(fileName).Dispose();
            
            RoutesResponse result = ComputeRoutesAsync().Result;
            
            if (result.Routes?.Count <= 0)
                return;
            
            string oldJson = File.ReadAllText(fileName);

            List<Route> oldRoutsList = [];
            if (!string.IsNullOrWhiteSpace(oldJson))
                oldRoutsList = JsonSerializer.Deserialize<RoutesResponse>(oldJson, JsonOptions)?.Routes ?? [];
            
            result.Routes?.AddRange(oldRoutsList);
            
            File.WriteAllText(fileName, JsonSerializer.Serialize(result, JsonOptions));
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Error: {ex.StatusCode} - {ex.Message}");
        }
    }

    private bool LoadConfig()
    {
        string configString = File.ReadAllText("config.json");
        Config config = JsonSerializer.Deserialize<Config>(configString, JsonOptions) ?? new Config();
        
        if (string.IsNullOrEmpty(config.GoogleApiKey) || string.IsNullOrEmpty(config.OriginAddress) || string.IsNullOrEmpty(config.DestinationAddress))
            return false;
        
        _key = config.GoogleApiKey;
        _originAddress = config.OriginAddress;
        _destinationAddress = config.DestinationAddress;
        
        return true;
    }
    
    private async Task<RoutesResponse> ComputeRoutesAsync()
    {
        string json = "";
        
        try
        {
            using HttpRequestMessage request = new(HttpMethod.Post, Url);
            request.Content = new StringContent(_requestBody, Encoding.UTF8, "application/json");
            request.Headers.Add("X-Goog-Api-Key", "AIzaSyCrQMbThAV4ZaXdq5-e82RcAJ5EEWmik_0");
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