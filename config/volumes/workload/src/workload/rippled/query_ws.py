from websocket import create_connection
import json
from time import sleep
# from rippled.logger import logging

# log = logging.getLogger(__name__)
url="rippled:6005" # docker network
# url=f"0.0.0.0:32777" # local forward

ws = create_connection(f"ws://{url}")

subscribe_command = {
  "command": "subscribe",
  "streams": [
      "ledger",
      "transactions",
      ]
}

ws.send(json.dumps(subscribe_command))

def main():
    while True:
        with open("subscribe_output.log", "a") as output:
            result =  ws.recv()
            # print(json.dumps(json.loads(result), indent=2))
            try:
                ledger_data = json.loads(result)
                txns = ledger_data.get("txn_count")
                if txns:
                    # log.info("%s transaction in ledger %s", txns, ledger_data.get("ledger_index"))
                    output.write(json.dumps(ledger_data, indent=2) + ",\n")
                # log.debug(ledger_data)

                # json.dump(result, output, ensure_ascii=True, indent=2)
            except json.decoder.JSONDecodeError as e:
                pass
                # log.error("ws.recv() received not json!")
                # log.error(e)
