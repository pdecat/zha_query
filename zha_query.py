import aiohttp
import argparse
import asyncio
import json
import logging
import os

ws_query_id = 1


parser = argparse.ArgumentParser(
    description="Query ZHA devices sw_build_id attribute ('Basic' cluster)"
)
parser.add_argument(
    "--log-level",
    default="ERROR",
    help="Set logging level (one of DEBUG, INFO, WARNING, ERROR or CRITICAL)",
)
parser.add_argument(
    "--case-sensitive",
    action="store_true",
    help="Be case sensitive when filtering devices by manufacturer, model or power-source",
)
parser.add_argument(
    "--manufacturer",
    default="",
    help="Filter by manufacturer name (e.g. IKEA, Legrand, OSRAM, etc.)",
)
parser.add_argument(
    "--model",
    default="",
    help="Filter by model name (e.g. Bulb, Dimmer, Plug, etc.)",
)
parser.add_argument(
    "--power-source",
    default="",
    help="Filter by power source type (e.g. Mains or Battery)",
)
args = parser.parse_args()

logging.basicConfig(level=logging.getLevelName(args.log_level.upper()))

logging.debug("main: args.case_sensitive=%s", args.case_sensitive)
logging.debug("main: args.manufacturer=%s", args.manufacturer)
logging.debug("main: args.model=%s", args.model)
logging.debug("main: args.power_source=%s", args.power_source)


async def read_ws(ws):
    msg = await ws.receive()
    logging.debug("read_ws: msg=%s", str(msg))
    if msg.type == aiohttp.WSMsgType.ERROR:
        raise msg
    elif msg.type == aiohttp.WSMsgType.CLOSED:
        raise msg
    if msg.type == aiohttp.WSMsgType.TEXT:
        return msg.json()
    return msg


async def call_ws(ws, data):
    logging.debug("call_ws: data=%s", data)
    if "zha/" in data["type"]:
        global ws_query_id
        data["id"] = ws_query_id
        ws_query_id += 1
    await ws.send_str(json.dumps(data))
    msg = await read_ws(ws)
    if msg["type"] == "auth_required":
        msg = await read_ws(ws)
        if msg["type"] != "auth_ok":
            raise Exception("Auth failed: " + msg)
    return msg


def filter_device(device, attribute):
    def case(val):
        return val if args.case_sensitive else val.upper()

    return case(getattr(args, attribute)) in case(device[attribute])


async def main():
    url = os.environ["HASSIO_URL"]
    access_token = os.environ["HASSIO_TOKEN"]

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            await call_ws(ws, {"type": "auth", "access_token": access_token})

            devices = await call_ws(ws, {"type": "zha/devices"})
            logging.debug("main: devices=%s", devices)

            for device in devices["result"]:
                if (
                    filter_device(device, "manufacturer")
                    and filter_device(device, "model")
                    and filter_device(device, "power_source")
                ):
                    clusters = await call_ws(
                        ws, {"type": "zha/devices/clusters", "ieee": device["ieee"]}
                    )
                    logging.debug("main: clusters=%s", clusters)
                    cluster_found = False
                    device_name = device["user_given_name"] or "%s %s" % (
                        device["manufacturer"].strip(),
                        device["model"].strip(),
                    )
                    for cluster in clusters["result"]:
                        if cluster["type"] == "in" and cluster["name"] == "Basic":
                            cluster_found = True
                            logging.debug(
                                "main: Querying sw_build_id for device %s (%s) on cluster %s (endpoint %s)",
                                device["ieee"],
                                device_name,
                                cluster["id"],
                                cluster["endpoint_id"],
                            )
                            resp = await call_ws(
                                ws,
                                {
                                    "type": "zha/devices/clusters/attributes/value",
                                    "ieee": device["ieee"],
                                    "endpoint_id": cluster["endpoint_id"],
                                    "cluster_id": cluster["id"],
                                    "cluster_type": "in",
                                    "attribute": 0x4000,
                                },
                            )
                            if resp["success"]:
                                print(
                                    "Device %s has sw_build_id %s (%s)"
                                    % (
                                        device["ieee"],
                                        resp["result"],
                                        device_name,
                                    )
                                )
                            else:
                                logging.error(
                                    "Failed to query sw_build_id for device %s (%s): %s",
                                    device["ieee"],
                                    device_name,
                                    resp,
                                )
                            break
                    if not cluster_found:
                        logging.warning(
                            "Did not find Basic cluster for device %s (%s)",
                            device["ieee"],
                            device_name,
                        )


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
