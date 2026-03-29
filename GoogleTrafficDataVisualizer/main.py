import json
import Routes
import dearpygui.dearpygui as dpg
from datetime import datetime, timedelta
import pyperclip as pcp
import webbrowser
import os
import glob

loaded_routes = list[Routes.Route]

def load_routes(filepath: str) -> list[Routes.Route]:
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

    return routes

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

def refresh_ui(routes: list[Routes.Route]):
    # Delete existing windows if they exist
    if dpg.does_item_exist("graph_window"):
        dpg.delete_item("graph_window")
    if dpg.does_item_exist("collapse_window"):
        dpg.delete_item("collapse_window")
    if dpg.does_item_exist("tooltip"):
        dpg.delete_item("tooltip")
    if dpg.does_item_exist("plot_handlers"):
        dpg.delete_item("plot_handlers")

    build_graph_ui(routes)
    build_collapsing_ui(routes)

def choose_new_routes(sender, app_data):
    global loaded_routes
    filepath = app_data["file_path_name"]
    loaded_routes = load_routes(filepath)
    refresh_ui(loaded_routes)


def build_graph_ui(routes: list[Routes.Route]):
    global loaded_routes

    sorted_routes = sorted(routes, key=lambda r: r.timestamp)

    x_values = [datetime.fromisoformat(r.timestamp).timestamp() for r in sorted_routes]
    y_values = [int(r.duration.replace("s", "")) for r in sorted_routes]

    # Thresholds for snapping to a point (in plot-space units)
    x_range = max(x_values) - min(x_values) if len(x_values) > 1 else 1
    y_range = max(y_values) - min(y_values) if len(y_values) > 1 else 1
    x_snap = x_range * 0.05
    y_snap = y_range * 0.15

    with dpg.window(label="Routes Graph", width=780, height=520, tag="graph_window"):
        dpg.add_text("Trip Duration Over Time")
        dpg.add_spacer(height=4)

        with dpg.plot(label="Duration (s) vs Timestamp", height=420, width=-1, tag="plot"):
            dpg.add_plot_legend()

            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Timestamp", scale=1)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Duration (seconds)")

            dpg.add_line_series(x_values, y_values, label="Duration", parent=y_axis)
            dpg.add_scatter_series(x_values, y_values, label="Captured points", parent=y_axis)

            dpg.set_axis_limits(y_axis, min(y_values) - 30, max(y_values) + 30)
            dpg.fit_axis_data(x_axis)

        dpg.add_button(label="Load file", callback=lambda: dpg.show_item("file_dialog_id"))

    # Floating tooltip window, hidden until hovering a point
    with dpg.window(tag="tooltip", height=10, show=False, no_title_bar=True, no_resize=True,
                    no_move=True, no_scrollbar=True, no_saved_settings=True):
        dpg.add_text("", tag="tooltip_text")

    def get_nearest_node():
        mx, my = dpg.get_plot_mouse_pos()

        # Find the nearest data point within snap threshold
        nearest = None
        nearest_dist = float("inf")
        for i, (x, y) in enumerate(zip(x_values, y_values)):
            if abs(mx - x) < x_snap and abs(my - y) < y_snap:
                dist = ((mx - x) ** 2 + (my - y) ** 2) ** 0.5
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = i

        return nearest

    def on_plot_hover():
        nearest = get_nearest_node()

        if nearest is not None:
            seconds = y_values[nearest]
            iso_duration = seconds_to_iso_duration(seconds)
            timestamp = sorted_routes[nearest].timestamp.split('.')[0]
            dpg.set_value("tooltip_text", f"Duration:  {iso_duration}\nTimestamp: {timestamp}")
            px, py = dpg.get_mouse_pos(local=False)
            dpg.configure_item("tooltip", show=True, pos=(int(px) + 12, int(py) + 12))
        else:
            dpg.configure_item("tooltip", show=False)

    def on_plot_click():
        nearest = get_nearest_node()

        if loaded_routes is None or nearest is None:
            dpg.configure_item("tooltip", show=False)
            return

        timestamp = sorted_routes[nearest].timestamp
        test = None

        for x in loaded_routes:
            if x.timestamp == timestamp:
                test = x

        if test is None:
            return

        pcp.copy(test.polyLine.encoded_polyline)
        webbrowser.open("https://developers.google.com/maps/documentation/utilities/polylineutility")

    with dpg.item_handler_registry(tag="plot_handlers"):
        dpg.add_item_hover_handler(callback=on_plot_hover)
        dpg.add_item_clicked_handler(callback=on_plot_click)

    dpg.bind_item_handler_registry("plot", "plot_handlers")

def build_collapsing_ui(routes: list[Routes.Route]):
    global loaded_routes

    def copy_clicked(encoded_polyline):
        if encoded_polyline is None:
            return

        pcp.copy(encoded_polyline)
        webbrowser.open("https://developers.google.com/maps/documentation/utilities/polylineutility")

    with dpg.window(label="Routes Collapse", width=780, height=520, collapsed=True, tag="collapse_window"):
        for i, route in enumerate(routes):
            with dpg.collapsing_header(label=f"Route {i + 1}"):
                dpg.add_text(f"Timestamp:  {route.timestamp}")
                dpg.add_text(f"Duration:   {route.duration_as_timespan}  ({route.duration})")
                dpg.add_text(f"Distance:   {route.distance_meters} m")
                dpg.add_button(label="Click to copy encoded polyline", callback=lambda: copy_clicked(route.polyLine.encoded_polyline))
                dpg.add_separator()

def main():
    global loaded_routes

    dpg.create_context()
    dpg.create_viewport(title="Routes Viewer", width=780, height=530)
    dpg.setup_dearpygui()

    with open("config.json", "r") as f:
        data = json.load(f)

    routes_folder_location = data["routesFolderLocation"]

    files = glob.glob(routes_folder_location + "*")
    latest = max(files, key=os.path.getctime)

    with dpg.file_dialog(directory_selector=False, show=False, callback=choose_new_routes, id="file_dialog_id",
                         width=700, height=400):
        dpg.add_file_extension(".json", color=(150, 255, 150, 255))

    loaded_routes = load_routes(latest)
    build_graph_ui(loaded_routes)
    build_collapsing_ui(loaded_routes)

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()