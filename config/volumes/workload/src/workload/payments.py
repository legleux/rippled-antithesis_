import asyncio
import json

from workload import logging
from workload.rippled.account import create_account, fund_account, pay, account_info, confirm_account

log = logging.getLogger(__name__)

def make_some_payments():
    log.info("Making some payments...")
    accounts = []

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        log.error(e)
        loop = asyncio.new_event_loop()

    for i in range(20):
        create_account_task = create_account()
        account =  loop.run_until_complete(create_account_task)
        log.debug("Generated account credentials: %s", account)
        account_id, secret = account

        fund_account_task = fund_account(account_id)
        log.info(f"Created account {account}")

        fund_account_response = loop.run_until_complete(fund_account_task)
        fund_account_raw_response = json.loads(fund_account_response)

        fund_account_response = fund_account_raw_response["result"]
        log.debug(f"{fund_account_response=}")
        if fund_account_raw_response["status"] == "success":
            confirm_account_task = confirm_account(account_id)
            account_exists = loop.run_until_complete(confirm_account_task)
            if account_exists:
                accounts.append(account)

        account_id, seed = accounts[-1]
        account_info_task = account_info(account_id)
        account_info_response = loop.run_until_complete(account_info_task)
        account_balance = account_info_response["Balance"]
        log.debug(f"{account_id=} {account_balance=}")

    source = accounts[0]
    destination = accounts[1]
    amount = 100000000
    pay_task = pay(source, destination, amount)
    pay_task_response = loop.run_until_complete(pay_task)
    log.debug("Payment response: %s", pay_task_response)
    log.debug(accounts)
    return accounts

async def get_account_info(account):
    log.info("Calling async account_info()")
    return await account_info(account)

def get_account_balances(accounts):
    balances = []
    for account in accounts:
        loop = asyncio.get_event_loop()
        account_info_task = account_info(account[0])
        account_info_response = loop.run_until_complete(account_info_task)
        log.debug(f"{account_info_response=}")
        account, balance = account_info_response["Account"], account_info_response["Balance"]
        balances.append({"account":account, "balance": balance})
    log.debug("Returning balances:")
    return balances

if __name__ == "__main__":
    accounts = make_some_payments()
    log.debug("make_some_payments() returned:")
    log.debug(accounts)
    accounts = get_account_balances(accounts)
    for account in accounts:
        address, balance = account['account'], account['balance']
        log.info(f"Account: {address}, Balance: {balance}")

# loop.close()
