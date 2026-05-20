import json
import Routes
import dearpygui.dearpygui as dpg
from datetime import datetime, timedelta
import pyperclip as pcp
import webbrowser
import os
import calendar
import os.path

routes_location = ""
loaded_routes = []
window_size = window_size_x, window_size_y = 1000, 600

def error_opening(message: str):
    with dpg.window(label="Error", width=400, height=200):
        dpg.add_text(message)

def get_config():
    global routes_location
    if not os.path.exists("config.json"):
        error_opening("No config found in executing directory")
        return

    with open("config.json", "r") as f:
        data = json.load(f)

    routes_location = data["routesFolderLocation"]

def get_week_start_end(date_input) -> list[str]:
    if isinstance(date_input, str):
        try:
            date_input = datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            date_input = datetime.now()

    days_to_subtract = date_input.weekday()
    start_date = date_input - timedelta(days=days_to_subtract)
    end_date = start_date + timedelta(days=7)

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    return [start_date, end_date]

def get_files_from_period(start_date: str, end_date: str) -> list[str]:
    global routes_location

    files_in_period = []

    all_files = os.listdir(routes_location)

    if all_files is None or all_files == []:
        error_opening("No files in directory")
        return None

    for file in all_files:
        date = file.split('_')[1]
        date = date.split('.')[0]

        if start_date <= date <= end_date:
            files_in_period.append(routes_location + file)

    return files_in_period

def load_routes(filepath: str) -> Routes.Routes:
    with open(filepath, "r") as f:
        data = json.load(f)

    routes = []
    for r in data["routes"]:
        poly_line = Routes.PolyLine(r["polyline"]["encodedPolyline"])
        route = Routes.Route(
            distance_meters=r["distanceMeters"],
            duration=r["duration"],
            duration_as_timespan=r["durationAsTimeSpan"],
            poly_line=poly_line,
            timestamp=r["timestamp"],
        )
        routes.append(route)

    routes = Routes.Routes(routes)

    return routes

def normalize_timestamp():
    global loaded_routes

    base_date = datetime(2000, 1, 1)

    for routes in loaded_routes:
        for route in routes.routes:
            dt = datetime.fromisoformat(route.timestamp)
            normalized_dt = base_date.replace(hour=dt.hour, minute=dt.minute, second=dt.second, microsecond=dt.microsecond)
            route.normalized_timestamp = normalized_dt.isoformat()

def seconds_to_iso_duration(seconds: int) -> str:
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = ""
    if hours:
        parts += f"{hours}H "
    if minutes:
        parts += f"{minutes}M "
    if secs or not (hours or minutes):
        parts += f"{secs}S"
    return parts

def refresh_ui():
    # Delete existing windows if they exist
    if dpg.does_item_exist("graph_window"):
        dpg.delete_item("graph_window")
    if dpg.does_item_exist("collapse_window"):
        dpg.delete_item("collapse_window")
    if dpg.does_item_exist("tooltip"):
        dpg.delete_item("tooltip")
    if dpg.does_item_exist("plot_handlers"):
        dpg.delete_item("plot_handlers")

    build_graph_ui()
    build_collapsing_ui()

def build_graph_ui(period: list[str]):
    global loaded_routes
    global window_size

    all_series = []

    for file_index, routes_obj in enumerate(loaded_routes):
        file_routes = routes_obj.routes
        if not file_routes:
            continue

        sorted_routes = sorted(file_routes, key=lambda r: r.timestamp)
        x_vals = [calendar.timegm(datetime.fromisoformat(r.normalized_timestamp).timetuple()) for r in sorted_routes]
        y_vals = [int(r.duration.replace("s", "")) for r in sorted_routes]

        label = f"File {file_index + 1}"
        all_series.append((x_vals, y_vals, sorted_routes, label))

    if not all_series:
        return

    # Compute global x/y range for snapping
    all_x = [x for s in all_series for x in s[0]]
    all_y = [y for s in all_series for y in s[1]]
    x_range = max(all_x) - min(all_x) if len(all_x) > 1 else 1
    y_range = max(all_y) - min(all_y) if len(all_y) > 1 else 1
    x_snap = x_range * 0.02
    y_snap = y_range * 0.02

    with dpg.window(label="Routes Graph", width=window_size[0], height=window_size[1],
                    tag="graph_window", no_close=True, no_move=True, no_resize=True):
        dpg.add_text(f"Trip Duration Over Time\nPeriod: {period[0]} - {period[1]}")
        dpg.add_spacer(height=4)

        with dpg.plot(label="Duration (s) vs Timestamp", height=420, width=-1, tag="plot"):
            dpg.add_plot_legend()

            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Timestamp", scale=1)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Duration (seconds)")

            # Plot each file as a separate line series
            for x_vals, y_vals, _, label in all_series:
                dpg.add_line_series(x_vals, y_vals, label=label, parent=y_axis)

            dpg.set_axis_limits(y_axis, min(all_y) - 30, max(all_y) + 30)
            dpg.fit_axis_data(x_axis)

    # Tooltip window
    with dpg.window(tag="tooltip", height=10, show=False, no_title_bar=True, no_resize=True,
                    no_move=True, no_scrollbar=True, no_saved_settings=True):
        dpg.add_text("", tag="tooltip_text")

    def get_nearest_node():
        mx, my = dpg.get_plot_mouse_pos()
        best_series_idx = None
        best_point_idx = None
        best_dist = float("inf")

        for s_idx, (x_vals, y_vals, _, _) in enumerate(all_series):
            for p_idx, (x, y) in enumerate(zip(x_vals, y_vals)):
                if abs(mx - x) < x_snap and abs(my - y) < y_snap:
                    dist = ((mx - x) ** 2 + (my - y) ** 2) ** 0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_series_idx = s_idx
                        best_point_idx = p_idx

        if best_series_idx is not None:
            return best_series_idx, best_point_idx
        return None

    def on_plot_hover():
        nearest = get_nearest_node()
        if nearest is not None:
            s_idx, p_idx = nearest
            seconds = all_series[s_idx][1][p_idx]
            iso_duration = seconds_to_iso_duration(seconds)
            timestamp = all_series[s_idx][2][p_idx].timestamp.split('.')[0]
            dpg.set_value("tooltip_text",
                          f"Duration:  {iso_duration}\nTimestamp: {timestamp.replace('T', ' ')}")
            px, py = dpg.get_mouse_pos(local=False)
            dpg.configure_item("tooltip", show=True, pos=(int(px) + 12, int(py) + 12))
        else:
            dpg.configure_item("tooltip", show=False)

    def on_plot_click():
        nearest = get_nearest_node()
        if nearest is None:
            return

        s_idx, p_idx = nearest
        route = all_series[s_idx][2][p_idx]
        pcp.copy(route.polyLine.encoded_polyline)
        webbrowser.open("https://developers.google.com/maps/documentation/utilities/polylineutility")

    with dpg.item_handler_registry(tag="plot_handlers"):
        dpg.add_item_hover_handler(callback=on_plot_hover)
        dpg.add_item_clicked_handler(callback=on_plot_click)

    dpg.bind_item_handler_registry("plot", "plot_handlers")
def build_collapsing_ui():
    global loaded_routes
    global window_size

    def copy_clicked(encoded_polyline):
        if encoded_polyline is None:
            return

        pcp.copy(encoded_polyline)
        webbrowser.open("https://developers.google.com/maps/documentation/utilities/polylineutility")

    with dpg.window(label="Routes Collapse", width=window_size[0], height=window_size[1], collapsed=True,
                    tag="collapse_window", no_close=True, no_move=True, no_resize=True):
        for i, routes_obj in enumerate(loaded_routes):
            if not routes_obj.routes:
                continue

            date_str = routes_obj.routes[0].timestamp.split('T')[0]
            with dpg.collapsing_header(label=f"Date: {date_str}"):
                for j, route in enumerate(routes_obj.routes):

                    time_str = route.timestamp.split('T')[1].split('.')[0]
                    with dpg.collapsing_header(label=f"Route {time_str}"):
                        dpg.add_text(f"Timestamp:  {route.timestamp.replace('T', ' ')}")
                        dpg.add_text(f"Duration:   {route.duration_as_timespan}  ({route.duration})")
                        dpg.add_text(f"Distance:   {route.distance_meters} m")
                        dpg.add_button(
                            label="Click to copy encoded polyline",
                            callback=lambda s, a, u=route.polyLine.encoded_polyline: copy_clicked(u)
                        )
                        dpg.add_separator()

def draw_all():
    global loaded_routes
    global routes_location

    get_config()

    if routes_location is None:
        return

    if not os.path.exists(routes_location):
        error_opening("No routes folder found.")
        return

    if routes_location[-1] != '/':
        routes_location += '/'

    period_start_end = get_week_start_end(datetime.today())
    files = get_files_from_period(period_start_end[0], period_start_end[1])

    for file in files:
        routes = load_routes(file)

        if routes is not None:
            loaded_routes.append(routes)

    normalize_timestamp()

    build_graph_ui(period_start_end)
    build_collapsing_ui()

def main():
    global loaded_routes
    global window_size

    dpg.create_context()
    dpg.create_viewport(title="Routes Viewer", width=window_size[0], height=window_size[1])
    dpg.setup_dearpygui()

    draw_all()

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()