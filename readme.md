## Connectify

This repo is hosting the Lambda code of the backend service for the Alexa skill **"Connectify""**

The Lambda is managing 2 intents :
- *ListDevices*
- *PlayOnDevice*

The *ListDevices* intent lists the user's registered devices in Spotify

The *PlayOnDevice* intent transfer playback to the Spotify device identified by the ordered number of *ListDevices* or by its name if it is a "common" name
