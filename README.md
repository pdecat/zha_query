# Query ZHA cluster attributes

This script uses the Home Assistant websocket API to query ZHA cluster attributes.

It currently only supports querying the sw_build_id attribute (id 0x4000/16384) from clusters named "Basic".

The Long-Lived Access Token used for authentication must be created from an admin user's profile.

Setup:

```
export HASSIO_TOKEN=******
export HASSIO_URL=http://localhost:8123/api/websocket
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Usage:

```
./venv/bin/python zha_query.py --help
usage: zha_query.py [-h] [--log-level LOG_LEVEL] [--case-sensitive] [--manufacturer MANUFACTURER] [--model MODEL] [--power-source POWER_SOURCE]

Query ZHA sw_build_id of devices.

optional arguments:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        Set logging level (one of DEBUG, INFO, WARNING, ERROR or CRITICAL)
  --case-sensitive      Be case sensitive when filtering devices by manufacturer, model or power-source
  --manufacturer MANUFACTURER
                        Filter by manufacturer name (e.g. IKEA, Legrand, OSRAM, etc.)
  --model MODEL         Filter by model name (e.g. Bulb, Dimmer, Plug, etc.)
  --power-source POWER_SOURCE
                        Filter by power source type (e.g. Mains or Battery)
```

Sample:
```
./venv/bin/python zha_query.py --manufacturer IKEA --power-source Mains --model bulb
```
