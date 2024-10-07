import json
import websockets
# from rippled.logger import logging
import sys
import asyncio
# log = logging.getLogger(__name__)


async def watch_for_new_accounts(accounts):
    ws_endpoint = "ws://rippled:6005"
    subscribe_to_ledger_payload = json.dumps({
        "command": "subscribe",
        "accounts": accounts,
        # "streams": ["transactions"],
    })
    async with websockets.connect(ws_endpoint) as websocket:
        # log.info("Subscribing to watch")

        await websocket.send(subscribe_to_ledger_payload)

# if __name__ == "__main__":
def main():
    args = sys.argv[1]
    # log.info("args %s", args)
    asyncio.run(watch_for_new_accounts(args))
