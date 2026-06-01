# Google Trafic data collection and visualization tool

This project is made to collect and visualize the time from a origin to a destination.

## Collection tool
The core part is being able to collect the data. This project uses the google routes API and C#

It looks for the `config.json` file in the executing directory.
The file should have this structure:
```
{
  "googleApiKey": "Key",
  "routesFolderLocation": "/Absolute/path/to/folder/",
  "originAddress": "Full address/google location code",
  "destinationAddress": "Full address/google location code"
}
```

I recommend setting up a CRON job to run the tool every 5 minutes. 

## visualization tool
The visualization tool is made with Python using DearPyGui.

It looks for the `config.json` file in the executing directory.
The file should have this structure:
```
{
  "routesFolderLocation": "/home/tristan/routes/",
  "window_x": 1000,
  "window_y": 600
}
```

It automatically opens the files in current week. you can then select a custom period by selecting it using the `Select Date Range` button.
It will create an average og the selected period, appropriately named `average` in the graph legend.

### Known bugs:
If there are no routes in the selected period, the `Select Date Range` button will not show, and it is impossible to select a new period
If you hide a day it will still show up when hovering where it would be if not hidden. 
