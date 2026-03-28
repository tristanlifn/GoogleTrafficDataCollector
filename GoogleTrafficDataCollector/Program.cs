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

    private static readonly HttpClient HttpClient = new();
    private const string Url = "https://routes.googleapis.com/directions/v2:computeRoutes";
    private const string Key = "";
    private const string DestinationAddress = "GFMC+36 Kolding, Denmark";
    private const string OriginAddress = "Stenholt 37, 6092 Sønder Stenderup, Denmark";

    private const string RequestBody = $$"""
                                         {
                                                     "computeAlternativeRoutes": false,
                                                     "destination": {
                                                         "address": "{{DestinationAddress}}"
                                                     },
                                                     "origin": {
                                                         "address": "{{OriginAddress}}"
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
        string documents = nameof(Environment.SpecialFolder.MyDocuments);
        string fileName = $"{documents}/routes.json";

        try
        {
            if (!File.Exists(fileName))
                File.Create(fileName).Dispose();
            
            RoutesResponse result = ComputeRoutesAsync().Result;
            
            string oldJson = File.ReadAllText(fileName);

            List<Route> oldRoutsList = [];
            if (!string.IsNullOrWhiteSpace(oldJson))
                oldRoutsList = JsonSerializer.Deserialize<RoutesResponse>(oldJson, JsonOptions)?.Routes ?? [];
            
            result.Routes.AddRange(oldRoutsList);
            
            File.WriteAllText(fileName, JsonSerializer.Serialize(result, JsonOptions));
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Error: {ex.StatusCode} - {ex.Message}");
        }
    }

    private static async Task<RoutesResponse> ComputeRoutesAsync()
    {
        string json = "";
        
        try
        {
            using HttpRequestMessage request = new(HttpMethod.Post, Url);
            request.Content = new StringContent(RequestBody, Encoding.UTF8, "application/json");
            request.Headers.Add("X-Goog-Api-Key", Key);
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