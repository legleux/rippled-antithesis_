# from rippled import rippled
from typing import Optional
from dataclasses import field, InitVar, dataclass
from types import SimpleNamespace
import asyncio
import json
from random import randrange
default_key_type = "secp"
import time
import requests
# from rippled.logger import logging
import websockets
from workload import logging
from xrpl.models import Payment
from xrpl.wallet import Wallet
from xrpl.constants import CryptoAlgorithm
from websocket import create_connection
from xrpl.transaction import sign
from xrpl.clients import JsonRpcClient
from xrpl.account import does_account_exist
from xrpl.transaction import sign_and_submit

log = logging.getLogger(__name__)

def get_network_base_fee(connection=None): # TODO: Implement
    return "12"

@dataclass
class Account:
    preseed: InitVar[Optional[str]] = None
    key_type: InitVar[Optional[str]] = None

    _master_seed: str = field(init=False)
    _account_id: str = field(init=False)
    _key_type: str = field(init=False)

    def __post_init__(self, preseed, key_type):
        if preseed is not None:
            log.debug(f"Got seed as {preseed}.")
            account = rippled.wallet_propose(preseed)
        else:
            log.debug("GOT NO SEED!!!")
            account = rippled.wallet_propose()
        self._master_seed, self._account_id = account
        self._key_type = key_type or default_key_type
        log.debug(f"Creating account {self}")


    def __str__(self):
        return f"{self._account_id}"

    def __repr__(self):
        return f"Acccount: account_id: [{self._account_id}], master_seed: [{self._master_seed}], key_type: [{self._key_type}]"

    @property
    def account_id(self):
        return self._account_id

    @property
    def master_seed(self):
        return self._master_seed

    @property
    def key(self):
        __key = SimpleNamespace()
        __key.type = self._key_type
        __key.smell = "good"
        return __key

    a = address = account_id
    s = seed = master_seed

genesis_account =  {
    "account_id": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "master_seed": "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
}


def compose_payment_payload(account, destination, amount=str(1_000_000000)):
    account_id, master_seed = account
    payload = {
        "TransactionType": "Payment",
        "Account": account_id,
        "Destination": destination,
        "Amount": amount,
    }
    if not payload.get("Fee"):
        payload["Fee"] = get_network_base_fee()
    # TODO: Don't do the dumps() here....
    return json.dumps({"command": "submit", "tx_json": payload, "secret": master_seed})

# ws_endpoint = "ws://rippled:6005"
# ws = websockets.connect(ws_endpoint)
# async with websockets.connect('ws://localhost:6789') as ws:
#     await ws.send('asdf')

async def make_payment(ws, wallet):
    payment_payload = compose_payment_payload(genesis_account, wallet)
    async with websockets.connect("ws://rippled:6005") as ws:
        response = await ws.send(payment_payload)
    payment_response = await ws.recv()
    payment_response = json.loads(payment_response)
    result = payment_response["result"]
    return result


# async def fund_account(destination):
#     url="rippled:6005" # docker network
#     ws = create_connection(f"ws://{url}")
#     secp = CryptoAlgorithm.SECP256K1
#     w = Wallet.from_secret(genesis_account["master_seed"], algorithm=secp)
#     payment_tx = Payment(account=w.address, amount=str(1000_000000), destination=destination)
#     # signed_txn = sign(payment_tx, w)
#     client = JsonRpcClient("http://rippled:5005")
#     return await sign_and_submit(payment_tx, client, w)

async def fund_account2(destination):
    ws_endpoint = "ws://rippled:6005"
    account = genesis_account["account_id"], genesis_account["master_seed"]
    pp = compose_payment_payload(account, destination)
    log.debug("Payment payload %s", pp)
    # payment_msg = json.dumps({
    #     "command": "submit",
    #     "tx_json": {**pp},
    #     "secret": account[1]
    # })
    # log.debug(pp)
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("Submitting %s", pp)
        await ws.send(pp)
        response = await ws.recv()
        log.debug("Received %s", response)
        return response

async def payment(source, destination, amount):
    def sign_transaction():
        # An Account object calls this method
        pass
    def submit_signed_payment_transaction(source, destination, transaction):
        # An Account object calls this method
        def submit_transaction():
            # A ClassMethod of an xrpld server
            # ws_endpoint = "ws://rippled:6005"
            pass

    payment_tx_json = compose_payment_payload(source, destination, amount)
    log.debug("payment_tx_json: %s", payment_tx_json)
    ws_endpoint = "ws://rippled:6005"
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("Submitting %s", payment_tx_json)
        await ws.send(payment_tx_json)
        response = await ws.recv()
        log.debug("Received %s", response)
        return response


# async def fee():
#     url="ws://rippled:6005" # docker network
#     ws = create_connection(f"ws://{url}")
#     ws.send(json.dumps({"command": "fee"}))
#     response_str = ws.recv()
#     response = json.loads(response_str)
#     if response["status"] == "success":
#         result = response.get("result")
#         return result
def fee() -> dict[str, str]:
    fee_method = {"method": "fee"}
    try:
        fee_response = requests.post("http://rippled:5005", json=fee_method)
        # log.debug("fee command response %s", fee_response)
        # log.debug("fee command json %s", fee_response.json())
        fee_response_json = fee_response.json()
        fee_result = fee_response_json.get("result")
        return fee_result
    except requests.exceptions.JSONDecodeError as e:
        error_msg = "Received no json"
        # log.error("Received no json")
        # log.error(e)
        return {error_msg: json.dumps(e)}

def get_ledger_info():
    ledger_info = fee()
    log_msg="\nLedger info\n**************\n"
    for field in [
        "current_ledger_size",
        "current_queue_size",
        "expected_ledger_size",
        "max_queue_size",
    ]:
        log_msg += f"{field}: {ledger_info[field]}\n"
    log_msg +=  f"open_ledger_level: {get_open_ledger_level()}\n"
    log_msg +=  f"open_ledger_fee: {get_open_ledger_fee()}\n"
    # log.info(log_msg.strip("\n"))

def get_queue_size() -> int:
    ledger_info = fee()
    return int(ledger_info.get("current_queue_size") or 0)

def get_open_ledger_fee() -> int:
    ledger_info = fee()
    drops = ledger_info["drops"]
    open_ledger_fee = drops.get("open_ledger_fee")
    # log.debug("Open ledger fee: %s", open_ledger_fee)
    return int(open_ledger_fee)

def get_open_ledger_level() -> int:
    ledger_info = fee()
    levels = ledger_info["levels"]
    open_ledger_level = levels.get("open_ledger_level")
    # log.debug("Open ledger fee: %s", open_ledger_level)
    return int(open_ledger_level)

def watch_fee():
    while True:
        get_ledger_info()
        time.sleep(0.05)

# async def get_ledger_info():
#     ledger_info = await fee()
#     for field in [
#         "current_ledger_size",
#         "current_queue_size",
#         "expected_ledger_size",
#         "max_queue_size",
#     ]:
#         log.info(ledger_info[field])

async def account_info(account_id):

    url="rippled:6005" # docker network
    ws = create_connection(f"ws://{url}")
    ws.send(json.dumps(
        {
            "command": "account_info",
            "account": account_id
        }))
    response_str = ws.recv()
    response = json.loads(response_str)
    result = response.get("result")
    account_data = result["account_data"]
    account_sequence = result["account_data"].get("Sequence")

    # payment_command = {
    #   "command": "subscribe",
    #   "streams": [
    #       "ledger",
    #       "transactions",
    #       ]
    # }
    # txn_json = {
    #     "TransactionType"
    # }
    # response = requests.post(f"http://rippled:5005", json={"method": "wallet_propose"})

async def create_account(n=1):
    try:
        response = requests.post("http://rippled:5005", json={"method": "wallet_propose"})
        raw_response = response.json()
        result = raw_response.get("result")
        account_id = result.get("account_id")
        master_seed = result.get("master_seed")
        account = account_id, master_seed
        # log.debug("generated: %s", account)
        return account
    except Exception as e:
        # log.error("wallet_propose() failed!")
        # log.error(e)
        raise
