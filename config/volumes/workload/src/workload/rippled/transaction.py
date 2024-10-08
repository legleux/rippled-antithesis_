DEFAULT_PAYMENT = 10_000_000000 # 10,000 XRP per account by default
async def send_payment(source, destination, amount: dict|int=DEFAULT_PAYMENT):
    source = source["account_id"]
    seed = source["master_seed"]
    destination = destination["account_id"]

    payment_payload = {
        "method": "submit",
        "params": [{
            "secret": ,
            "tx_json": {
                "TransactionType": "Payment",
                "Account": source,
                "Destination": destination,
                "Amount": amount,
                # "Sequence": 1
            }
        }]
    }

    try:
        wait = 3
        response = s.post(url, json=payment_payload)
        result = response.json()["result"]
        while result.get("error") == "highFee":
            print("Waiting for fee to die down.")
            await wait_for_n_ledgers(wait)
            response = s.post(url, json=payment_payload)
            result = response.json()["result"]
            if result.get("error") == "highFee":
                wait += 1
        # log.debug(json.dumps(result, indent=2))
        return result
    except Exception as e:
        log.error(repr(e))
        raise

async def create_trustline(account, amount, limit=1e15):
    trustline_limit = dict(amount, value=str(int(limit)))

    log.debug((f"Creating Trustline for {account.account_id} for {limit} {amount['currency']}"))
    log.debug(f"\tissued by: {amount['issuer']}")

    trustset_payload = {
        "method": "submit",
        "params": [{
            "tx_json": {
                "TransactionType": "TrustSet",
                "Account": account.account_id,
                "LimitAmount": trustline_limit
            },
            "secret": account.seed
        }]
    }
    try:
        response = s.post(url, json=trustset_payload)
        result = response.json()["result"]
        await wait_for_next_ledger()
        return result
    except Exception as e:
        log.error(repr(e))
        raise

async def distribute_currency(source, destination, currency: str="USD", amount: str="1000"):
    token = {
        "issuer": source.account_id,
        "currency": currency,
        }
    await asyncio.sleep(3)
    result = await create_trustline(destination, token)
    payment_amount = dict(token, value=amount)
    await send_payment(destination, source, payment_amount)

async def mint_nft(account, taxon=0):
    payload = {
        "method": "submit",
        "params": [{
            "tx_json": {
                "TransactionType": "NFTokenMint",
                "Account": account.account_id,
                "NFTokenTaxon": taxon
            },
            "secret": account.seed
        }]
    }
    mint_response = s.post(url, json=payload)
    log.debug(mint_response)
    if mint_response.json()["result"]["status"] == "success":
        log.debug(mint_response.json()["result"])
        log.debug("Minted nft")
    return mint_response
