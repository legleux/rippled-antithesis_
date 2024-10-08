import asyncio
import json
import sys

import websockets

# import logging

# logger = logging.getLogger('websockets')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())
genesis_account = {"account_id": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh", "seed": "snoPBrXtMeMyMHUVTgbuqAfg1SUTb"}
devnet = {
    "ip": "127.0.0.1",
    "ws_port": 6006,
}
local = {
    "ip": "172.30.0.6",
    "rpc": "5005",
    "ws_port": 6005,
}

ws_endpoint = f"ws://{local["ip"]}:{local["ws_port"]}"
connection = websockets.connect(uri=ws_endpoint)

ledger_cmd = {"command": "ledger_closed"}
ledger_subscribe = json.dumps({
  "id": "Example watch for new validated ledgers",
  "command": "subscribe",
  "streams": ["ledger"]
})


def get_payment_payload(account, destination, amount=str(1_000_000000)):
    if isinstance(destination, dict):
        destination = destination["account_id"]
    payload = {
        "TransactionType": "Payment",
        "Account": account["account_id"],
        "Destination": destination,
        "Amount": amount,
        "Fee": "12",
    }
    return json.dumps({"command": "submit", "tx_json": payload, "secret": account["seed"]})


def get_account_info_payload(account):
    account_info = {
      "command": "account_info",
      "account": account,
      "ledger_index": "current",
    #   "queue": true
    }
    return json.dumps(account_info)

# async def watch_ledger(ws_endpoint):
#     message = json.dumps(dict((ledger_cmd), id="1"))
#     async with websockets.connect(ws_endpoint) as websocket:
#         await websocket.send(message)
#         greeting = await websocket.recv()
#         print(f"Received: {greeting}")


async def consumer(websocket):
    pass
    data = await websocket.recv()
    print(data)


async def legder_subscription(ws_endpoint):
    async with websockets.connect(ws_endpoint) as websocket:
        await websocket.send(ledger_subscribe)
        async for message in websocket:
            await consumer(websocket)


async def send_command(ws_endpoint, command):
    async with websockets.connect(ws_endpoint) as websocket:
        await websocket.send(command)
        print("doin stuff")
        async for message in websocket:
            await consumer(websocket)


async def send_message(websocket, message):
    async with websockets.connect(ws_endpoint) as websocket:
        await websocket.send(message)
        print(f"sending message: {message}")
        async for message in websocket:
            await consumer(websocket)


async def wallet_propose(ws):
    wallet_propose_payload = json.dumps({"command": "wallet_propose"})
    await ws.send(wallet_propose_payload)
    wallet_propose_response = await ws.recv()
    wallet_data = json.loads(wallet_propose_response)["result"]
    wallet = {key: value for key, value in wallet_data.items() if key in ["account_id", "master_seed"]}
    return wallet


async def make_payment(ws, wallet):
    payment_payload = get_payment_payload(genesis_account, wallet, amount=str(1_000_000000))
    await ws.send(payment_payload)
    payment_response = await ws.recv()
    payment_result = json.loads(payment_response)["result"]
    return payment_result


async def watch_for_new_accounts(accounts):

    subscribe_to_ledger_payload = json.dumps({
        "id": "Example watch for new validated ledgers",
        "command": "subscribe",
        "accounts": accounts,
        # "streams": ["transactions"],
    })
    async with websockets.connect(ws_endpoint) as websocket:
        print("Subscribing to watch")
        await websocket.send(subscribe_to_ledger_payload)


async def check_for_accounts(ws):
            response = await ws.recv()
            print(f"reponse was:\n{response}")
            # async for message in websocket:
            #     await consumer(websocket)
    # await ws.send(subscribe_to_ledger_payload)
    # payment_response = await ws.recv()
    # payment_result = json.loads(payment_response)["result"]
    # return payment_result
    pass


async def confirm_account_creation(ws, account):
    account_info_payload = {
        "command": "account_info",
        "account": account["account_id"],
        "ledger_index": "current",
        # "queue": true
    }
    await ws.send(account_info_payload)
    account_info_response = await ws.recv()
    account_info_result = json.loads(account_info_response)["result"]
    return account_info_result

async def create_accounts():
    # msg = await ws.recv()
    ws = await websockets.connect(ws_endpoint)
    wallet = await wallet_propose(ws)
    payment_response = await make_payment(ws, wallet)
    account = "ragfZJ7rSSyYP9cgSvXvGBkp4j5gBvUifq"
    payment_response = await make_payment(ws, account)
    watch_for_new_accounts()
    await asyncio.gather(test1(), test2(), test3())
    pass


async def main():
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    create_accounts()
    start_light = asyncio.create_task(calculate_idle(3, event))
    await asyncio.gather(init_connection(message, event), start_light)


# account = "ragfZJ7rSSyYP9cgSvXvGBkp4j5gBvUifq"
if __name__ == "__main__":
    # if len(sys.argv) > 1 and sys.argv[1] == "w":
    asyncio.run(watch_for_new_accounts())
    asyncio.run(main())

    # if len(sys.argv) > 1 and sys.argv[1] == "c":
