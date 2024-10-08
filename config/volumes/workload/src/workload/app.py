import asyncio
import time

from random import SystemRandom

from workload import logging, check_check
from workload.rippled.account import (
    create_account, fund_account, fee, get_open_ledger_fee, account_info, mint_nft, queue_is_empty, is_fee_normal, confirm_account, get_current_queue_size
    )

log = logging.getLogger(__name__)

HIGH_FEE_BLOCKED_TIME = 10 # warning for being blocked from high fees
max_iterations = 300
errors = {}

urand = SystemRandom()
randrange = urand.randrange
sample = urand.sample

def get_base_fee_level(): # TODO: Implement this
    return 10

async def run_workload() -> int:
    start_time = int(time.time())
    accounts = []
    accounts_to_create = 500

    while len(accounts) < accounts_to_create:
        sleep_time = 0.1
        account = await create_account()
        log.debug("Created %s", account[0])
        if not int(time.time()) - start_time % 10 and sleep_time > 0.005:
            sleep_time -= 0.01
            log.info("Sleep time reduced to: %s",  sleep_time)
        time.sleep(sleep_time)

        def wait_for_next_ledger(): # TODO: Rename to something more accurate
            max_queue_size = 5
            queue_waited = 0
            def wait_for_base_fee():
                base_fee_level = get_base_fee_level()
                open_ledger_fee = get_open_ledger_fee()
                high_fee_times = []

                while open_ledger_fee > base_fee_level:
                    high_fee_times.append({"start": int(time.time())})
                    log.info(f"open_ledger_fee=[{open_ledger_fee}]! Sleeping until open_ledger_fee returns to {base_fee_level}.")
                    time.sleep(3)
                    open_ledger_fee = get_open_ledger_fee()
                    if (high_fee_time:=int(time.time()) - high_fee_times[-1].get("start")) > HIGH_FEE_BLOCKED_TIME:
                        log.critical("Been sleeping for %s due to open_ledger_fee being %s", high_fee_time, open_ledger_fee)
                    else:
                        log.info(f"{high_fee_time=}") # FIX: This doesn't work!

            wait_for_base_fee()

            while (current_queue_size := get_current_queue_size()) > max_queue_size:
                queue_waited += 1
                log.info(f"{current_queue_size=}")
                log.info(f"Sleeping until queue less than {max_queue_size}.")
                if queue_waited > 10:
                    max_queue_size += 5
                    queue_waited = 0
                    log.info("max_queue_size: %s", max_queue_size)
                    log.debug("queue_waited: %s", queue_waited)
                time.sleep(3)
            if queue_waited:
                log.info("Queue and/or Fees chilled out.")

        wait_for_next_ledger()

        accounts.append(account)
        last_account = accounts[-1]
        account_id = last_account[0]
        log.debug("Funding %s", account_id)
        response = await fund_account(account_id)
        confirmed = await confirm_account(account_id)
        if not confirmed:
            log.error("Couldn't confirm %-34s was created!", account_id)
        log.info("Funded %-34s", account_id )


    for account in accounts:
        account_info_ = await account_info(account[0])
        log.debug(f"{account_info_=}")
    runtime = int(time.time()) - start_time
    log.info(f"Created: {len(accounts)} accounts in {runtime} seconds")

    [minter] = sample(accounts, 1) # BUG: this is the same every time
    minter_info = await account_info(minter[0])
    log.info("Minter info: %s", minter_info)
    empty_queue = queue_is_empty()
    normal_fee = is_fee_normal()
    nfts_to_mint = range(len(accounts) * 5) # Some random number
    log.info("Trying to mint %s NFTs.", len(nfts_to_mint))
    for idx, _ in enumerate(nfts_to_mint):
        log.debug(f"{empty_queue=}")
        log.debug(f"{normal_fee=}")
        if empty_queue and normal_fee:
            response = await mint_nft(minter)
            result = response["result"]
            log.debug(result)
            if result["engine_result_code"] != 0:
                log.error(response)
                errors[result["engine_result_code"]] = errors[result["engine_result_code"]] + 1 if errors.get(result["engine_result_code"]) else 1
            else:
                log.debug(f"{minter} minted NFT!") # TODO: Prove it, bc I don't believe it.
                log.debug(result)
            wait_for_next_ledger()
            empty_queue = queue_is_empty()
            log.debug(f"{empty_queue=}")
            normal_fee = is_fee_normal()

    runtime = int(time.time()) - start_time
    log.info(f"Main workload finished after {runtime} seconds.")
    if errors:
        log.error("Errors:")
        for error in errors:
            log.error(error)
    return 0

def run():
    workload_run_start_time = time.time()
    iteration = 1
    while iteration <= max_iterations:
        check_check.main()
        asyncio.run(run_workload())
        log.debug("Iteration %s complete.", iteration)
        iteration += 1
    log.info("Total workload runtime: %s", int(time.time() - workload_run_start_time))
