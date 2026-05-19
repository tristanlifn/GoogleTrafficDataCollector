class Routes:
    def __init__(self, routes: list[Route]):
        self.routes = routes

    def append(self, route: Route):
        self.routes.append(route)

class PolyLine:
    def __init__(self, encoded_polyline):
        self.encoded_polyline = encoded_polyline

class Route:
    def __init__(self, distance_meters, duration, duration_as_timespan, poly_line, timestamp):
        self.distance_meters = distance_meters
        self.duration = duration
        self.duration_as_timespan = duration_as_timespan
        self.polyLine = poly_line
        self.timestamp = timestamp