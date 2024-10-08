import asyncio
import json
import time

from requests import post

from workload import logging
from workload.rippled.account import check_create, check_cash
from workload.payments import make_some_payments

log = logging.getLogger(__name__)

def send_check():
    accounts = make_some_payments()
    source = accounts[0]
    destination = accounts[1]
    amount = "100000000"
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        loop = asyncio.new_event_loop()
    log.debug(f"{source=}")
    log.debug(f"{destination=}")
    log.debug(f"{amount=}")
    checkcreate_task = check_create(source, destination[0], amount)
    check_response = loop.run_until_complete(checkcreate_task)
    return check_response, destination

def cash_check(account, check_id, amount):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        loop = asyncio.new_event_loop()
    cash_check_task = check_cash(account, check_id, amount)
    cash_check_response = loop.run_until_complete(cash_check_task)
    return cash_check_response

def tx(tx_json):
    retries_left = max_retries = 5
    wait = 3 # TODO: Wait for ledger
    while retries_left:
        txn_hash = tx_json["hash"]
        tx = {"method": "tx", "params": [{"transaction":  txn_hash}]}
        raw_response = post("http://rippled:5005", json=tx)
        time.sleep(wait)
        try:
            response = raw_response.json()
            result = response["result"]
            if not raw_response.ok:
                err_msg = f"Bad response from tx(): {response}"
                log.error(err_msg)
                raise Exception(err_msg)
            if result.get('meta'):
                if retries_left != max_retries:
                    log.info(f"Found it on try {max_retries - retries_left}")
                return result
            else:
                log.error("No 'meta' key in tx response!")
                log.info(f"{result=}")
                retries_left -=1
        except AttributeError as e:
            log.error(e)
            retries_left -= 1
    log.debug("Retries left: %s", retries_left)
    raise Exception("Couldn't find txn: %s", txn_hash)


def main():
    try:
        raw_response, check_receiver = send_check()
        log.debug(f"{check_receiver=}")
        time.sleep(6)
        log.debug(f"{raw_response=}")
        response = json.loads(raw_response)
        result = response['result']
        log.debug(json.dumps(result, indent=2))
        tx_json = result["tx_json"]

        amount = tx_json["SendMax"]

        tx_response = tx(tx_json)
        meta = tx_response["meta"]
        [check_ledger_index] = [cn["LedgerIndex"] for node in meta["AffectedNodes"] if (cn:=node.get("CreatedNode")) and cn.get("LedgerEntryType") == "Check"]
        log.debug(f"{check_ledger_index=}")
        cash_check_response = cash_check(check_receiver, check_ledger_index, amount)
        log.info(cash_check_response)
    except KeyError as e:
        log.error("send_check() failed: %s", raw_response)
