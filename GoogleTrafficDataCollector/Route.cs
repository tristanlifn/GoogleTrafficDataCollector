namespace GoogleTrafficDataCollector;

public class Route(int distanceMeters, string duration, PolyLine polyline)
{
    public int DistanceMeters { get; set; } = distanceMeters;
    public string Duration { get; set; } = duration;
    public PolyLine Polyline { get; set; } = polyline;
    public DateTime Timestamp { get; set; } = DateTime.Now;

    public TimeSpan DurationAsTimeSpan =>
        TimeSpan.FromSeconds(double.Parse(Duration.TrimEnd('s')));
}

public class PolyLine
{
    public string EncodedPolyline { get; set; }
}