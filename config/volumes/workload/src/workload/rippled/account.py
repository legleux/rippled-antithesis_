import time
import requests
import websockets
import json
from websocket import create_connection
from typing import Optional
from dataclasses import field, InitVar, dataclass
from types import SimpleNamespace

from workload import logging

log = logging.getLogger(__name__)

def get_network_base_fee(connection=None): # TODO: Implement
    return 10

base_fee = get_network_base_fee()

genesis_account =  {
    "account_id": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "master_seed": "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
}

def compose_nft_mint_payload(account):
    nft_defaults = {
        "TransferFee": 100,
        "NFTokenTaxon": 0,
        "Flags": 8,
        "URI": "697066733A2F2F62616679626569676479727A74357366703775646D37687537367568377932366E6634646675796C71616266336F636C67747179353566627A6469",
        "Memos": [{
            "Memo": {
                "MemoType":
                  "687474703A2F2F6578616D706C652E636F6D2F6D656D6F2F67656E65726963",
                "MemoData": "72656E74"
            }
        }]
    }

    account_id, master_seed = account
    payload = {
        "TransactionType": "NFTokenMint",
        "Account": account_id,
        **nft_defaults,
    }

    if not payload.get("Fee"):
        payload["Fee"] = get_network_base_fee()

    return {"command": "submit", "tx_json": payload, "secret": master_seed}

async def mint_nft(account):
    nft_mint_tx_json = compose_nft_mint_payload(account)
    ws_endpoint = "ws://rippled:6005"
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("Minting NFT %s", nft_mint_tx_json)
        await ws.send(json.dumps(nft_mint_tx_json))
        response = await ws.recv()
        log.debug("Received %s", response)
        return json.loads(response)

def compose_check_payload(source, destination, send_max):
    account_id, master_seed = source
    payload = {
        "TransactionType": "CheckCreate",
        "Account": account_id,
        "Destination": destination,
        "SendMax": send_max,
    }

    log.debug("CheckCreate payload json: %s", payload)
    return {"command": "submit", "tx_json": payload, "secret": master_seed}

async def check_create(source, destination, send_max):
    check_create_json = compose_check_payload(source, destination, send_max)
    ws_endpoint = "ws://rippled:6005"
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("CheckCreate %s", check_create_json)
        await ws.send(json.dumps(check_create_json))
        response = await ws.recv()
        log.debug("Received %s", response)
        return response

def compose_check_cash_payload(source, check_id, amount):
    account_id, master_seed = source

    payload = {
        "TransactionType": "CheckCash",
        "Account": account_id,
        "CheckID": check_id,
        "Amount": amount,
    }
    if amount is not None:
        payload["Amount"] = amount
    log.debug("CheckCash payload json: %s", payload)
    return {"command": "submit", "tx_json": payload, "secret": master_seed}

async def check_cash(source, check_id, amount):
    check_create_json = compose_check_cash_payload(source, check_id, amount)
    ws_endpoint = "ws://rippled:6005"
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("CheckCreate %s", check_create_json)
        await ws.send(json.dumps(check_create_json))
        response = await ws.recv()
        log.debug("Received %s", response)
        return response

def compose_payment_payload(source, destination, amount=1_000_000000):
    account_id, master_seed = source
    if not isinstance(amount, str):
        amount = str(amount)
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

async def make_payment(ws, wallet):
    payment_payload = compose_payment_payload(genesis_account, wallet)
    async with websockets.connect("ws://rippled:6005") as ws:
        response = await ws.send(payment_payload)
    payment_response = await ws.recv()
    payment_response = json.loads(payment_response)
    result = payment_response["result"]
    return result

async def fund_account(destination):
    ws_endpoint = "ws://rippled:6005"
    account = genesis_account["account_id"], genesis_account["master_seed"]
    pp = compose_payment_payload(account, destination)
    log.debug("Payment payload %s", pp)
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("Submitting %s", pp)
        await ws.send(pp)
        response = await ws.recv()
        log.debug("Received %s", response)
        return response

async def pay(source, destination, amount):
    def sign_transaction():
        # An Account object calls this method
        pass
    def submit_signed_payment_transaction(source, destination, transaction):
        # An Account object calls this method
        def submit_transaction():
            # A ClassMethod of an xrpld server
            # ws_endpoint = "ws://rippled:6005"
            pass

    if not isinstance(destination, str):
        destination = destination[0]
    payment_tx_json = compose_payment_payload(source, destination, amount)
    log.debug("payment_tx_json: %s", payment_tx_json)
    ws_endpoint = "ws://rippled:6005"
    async with websockets.connect(ws_endpoint) as ws:
        log.debug("Submitting %s", payment_tx_json)
        await ws.send(payment_tx_json)
        response = await ws.recv()
        log.debug("Received %s", response)
        return response

def fee() -> dict[str, str]:
    fee_method = {"method": "fee"}
    try:
        fee_response = requests.post("http://rippled:5005", json=fee_method)
        fee_response_json = fee_response.json()
        fee_result = fee_response_json.get("result")
        log.debug("fee() %s", fee_result)
        return fee_result
    except requests.exceptions.JSONDecodeError as e:
        error_msg = "Received no json"
        return {error_msg: json.dumps(e)}

def get_ledger_info():
    ledger_info = fee()
    log_msg="\nLedger info\n**************\n"
    for li_field in [
        "current_ledger_size",
        "current_queue_size",
        "expected_ledger_size",
        "max_queue_size",
    ]:
        log_msg += f"{li_field}: {ledger_info[li_field]}\n"
    log_msg +=  f"open_ledger_level: {get_open_ledger_level()}\n"
    log_msg +=  f"open_ledger_fee: {get_open_ledger_fee()}\n"

def get_current_queue_size() -> int:
    ledger_info = fee()
    current_queue_size = int(ledger_info.get("current_queue_size"))
    log.debug(f"{current_queue_size=}")
    return current_queue_size

def queue_is_empty():
    current_queue_size = get_current_queue_size()
    log.debug(f"{current_queue_size=}")
    return current_queue_size == 0

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

def is_fee_normal():
    fee_is_base_fee = get_open_ledger_fee() == get_network_base_fee()
    log.debug(f"{fee_is_base_fee}")
    return fee_is_base_fee

def watch_fee():
    while True:
        get_ledger_info()
        time.sleep(0.05)

async def account_info(account_id):
    log.debug(f"Getting account_info for {account_id}")
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
    try:
        account_data = result["account_data"]
        # account_sequence = result["account_data"].get("Sequence")
        log.debug("Account data: %s", account_data)
        return account_data
    except Exception as e:
        raise

async def confirm_account(account_id):
    account_data = await account_info(account_id)
    log.debug(f"Account {account_id} exists!")
    return account_data is not None

async def create_account(n=1):
    try:
        response = requests.post("http://rippled:5005", json={"method": "wallet_propose"})
        raw_response = response.json()
        result = raw_response.get("result")
        account_id = result.get("account_id")
        master_seed = result.get("master_seed")
        account = account_id, master_seed
        log.debug("generated: %s", account)
        return account
    except Exception as e:
        log.error("wallet_propose() failed!")
        log.error(e)
        raise
