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

I recommend seting up a CRON job to run the tool every 5 minuts on a server, it does not need to be a powerfull or dedicated server. 

## visualization tool
The visualization tool is made with Python using DearPyGui.

It looks for the `config.json` file in the executing directory.
The file should have this structure:
```
{
  "routesFolderLocation": "/Absolute/path/to/folder/"
}
```

It automatically openes the newest created file int the configured path. You can manually open other files.
