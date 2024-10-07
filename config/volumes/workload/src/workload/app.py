import asyncio
from workload import logging
from workload.rippled.account import create_account, fund_account2, fee, get_open_ledger_fee
import argparse
import time
import json
from enum import StrEnum, auto
from dataclasses import dataclass, field
from typing import Optional

HIGH_FEE_BLOCKED_TIME = 10 # warning for being blocked from high fees

# class WorkloadState(StrEnum):
#     STARTING = auto()
#     RUNNING = auto()
#     BLOCKED = auto()

# class StateReason(StrEnum):
#     HIGHFEE = auto()
#     BLOCKED = auto()
#     QUEUED = auto()

# @dataclass
# class State:
#     state: WorkloadState = field(default=WorkloadState.STARTING)
#     reason: StateReason = field(init=False)
#     def __str__(self):
#         return self.state.value
#     @property
#     def running(self) -> WorkloadState:
#         return self.state
#     @running.setter
#     def running(self, value=WorkloadState.RUNNING):
#         print("setting state to running")
#         self.state = value

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Set logging to DEBUG")
    return parser.parse_args()

async def run_workload() -> int:
    # workload_state = State()
    args = parse_args()
    log = logging.getLogger(__name__)
    if args.debug:
        log.info("Got debug ")
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
    log.info("Starting app!")
    log.debug("I should be debug level!")
    # log.setLevel(debug_level)
    log.info("Starting workload...")
    # Create 5 "gateways"
    # print("doin stuff")
    account = await create_account()
    account_create_tasks = []
    async with asyncio.TaskGroup() as tg:
        for i in range(1, 21):
            account_create_tasks.append(tg.create_task(
                create_account(i)
            ))
    account_ids = []
    for idx, task in enumerate(account_create_tasks):
        result = task.result()
        account_id = result[0]
        account_ids.append(account_id)
        log.debug(f"Task {idx} result: {task.result()}")
        log.info(f"Task {idx} result: {task.result()}")

    log.info("Account ids: %s", account_ids)

    timings = [5, 4, 3, 2, 1, 0.5, 0.2, 0.1, 0.075, 0.05, 0.025, 0.0125, 0.00625]
    log.info(f"Trying to create {len(timings)} accounts with intervals: {timings}")
    for idx, i in enumerate(timings):
        time.sleep(i)
        response = await fund_account2(account_ids[idx])
        response = json.loads(response)
        result = response.get("result")
        if result.get("engine_result_code"):
            # log.error("Error! Bad result:\n%s", result)
            log.error("engine_result %s", result.get("engine_result"))
            log.error("engine_result_message %s", result.get("engine_result_message"))
        log.info(response)
    start = time.time()
    sleep_time = 0.1
    max_queue_size = 5
    queue_waited = 0
    queued = high_fee = False
    high_fee_times = []
    base_fee_level = 10 # get_base_fee_level() # TODO: implement. Get from network
    while True:
        account = await create_account()
        log.debug("Created %s", account[0])
        if not int(time.time() - start) % 10 and sleep_time > 0.005:
            sleep_time -= 0.01
            log.info("Sleep time reduced to: %s",  sleep_time)
        time.sleep(sleep_time)
        current_queue_size = int(fee()["current_queue_size"])
        open_ledger_fee = get_open_ledger_fee()
        # if current_queue_size == expected_queue_size:
            # time.sleep(3) # wait_for_next_ledger() TODO:
        while open_ledger_fee > base_fee_level:
            high_fee = True
            high_fee_times.append({"start": time.time.now()})
            log.info(f"{open_ledger_fee=}")
            log.info(f"Sleeping until open_ledger_fee returns to {base_fee_level}.")
            time.sleep(3)
            open_ledger_fee = get_open_ledger_fee()

            if (high_fee_time:=time.time() - high_fee_times[-1].get("start")) > HIGH_FEE_BLOCKED_TIME:
                log.critical("Been sleeping for %s due to open_ledger_fee being %s", high_fee_time, open_ledger_fee)
        high_fee = False
        high_fee_end_time = time.time()
        high_fee_times[-1].update({"close": high_fee_end_time, "length": int(high_fee_end_time - high_fee_times[-1]["start"])})
        while current_queue_size > max_queue_size:
            queued = True
            queue_waited += 1
            log.info(f"{current_queue_size=}")
            log.info(f"Sleeping until queue less than {max_queue_size}.")
            if queue_waited > 10:
                max_queue_size += 5
                queue_waited = 0
                log.info("max_queue_size: %s", max_queue_size)
                log.debug("queue_waited: %s", queue_waited)
            time.sleep(1)

        response = await fund_account2(account[0])
    return 0

def run():
    asyncio.run(run_workload())
