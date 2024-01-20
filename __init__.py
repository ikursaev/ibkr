import aiohttp
import asyncio
import dataclasses as dc


ideal = {
    "XIC": .3,
    "VUN": .3,
    "AVUV": .1,
    "XEF": .16,
    "AVDV": .06,
    "XEC": .08,
}


counterparts = {
    "VUN": "VTI",
    "XEF": "IEFA",
    "XEC": "IEMG"
}


PREFER_COUNTERPARTS = True


@dc.dataclass
class Position:
    symbol: str
    value: float
    exchange_rate: float
    price_in_usd: float
    currency: str
    quantity: int
    percent_ideal: float = .0
    percent_real: float = .0
    sum_to_rebalance: float = .0
    quantity_to_rebalance: int = 0
    counterpart: 'Position|None' = None

uri = "https://localhost:5000"

api_uri = f"{uri}/v1/api/"

async def get_account_id(session) -> str:
    async with session.get("/v1/api/portfolio/accounts") as accounts:
        accounts = await accounts.json()
        return accounts[0]["accountId"]


async def get_cash(session, account_id) -> dict:
    async with session.get(f"/v1/api/portfolio/{account_id}/ledger") as cash:
        return await cash.json()


async def get_portfolio(session, account_id) -> dict:
    async with session.get(f"/v1/api/portfolio/{account_id}/positions/0") as portfolio:
        return await portfolio.json()


positions: dict[str, Position] = {}


async def main():
    async with aiohttp.ClientSession(uri, connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        account_id = await get_account_id(session)
        cash = await get_cash(session, account_id)
        portfolio = await get_portfolio(session, account_id)

        total_in_usd = .0
        total_in_cad = .0
        total_cad_to_usd = .0

        counterpart_tickers = set(counterparts.values())

        for asset in portfolio:
            currency = asset["currency"]
            exchange_rate = cash[currency]["exchangerate"]

            value = asset["mktValue"]

            value_in_usd = exchange_rate * asset["mktValue"]
            price_in_usd = exchange_rate * asset["mktPrice"]

            positions[asset["ticker"]] = Position(
                asset["ticker"],
                value,
                exchange_rate,
                price_in_usd,
                asset["currency"],
                int(asset["position"]),
                percent_ideal=ideal.get(asset["ticker"], .0)
            )

            total_in_usd += value_in_usd

            if currency == "CAD":
                total_in_cad += value
                total_cad_to_usd += value * exchange_rate

        cash_to_rebalance = .0
        for currency, value in cash.items():
            if currency == "BASE":
                cash_to_rebalance = value["settledcash"]
                break

        total_with_rebalance = cash_to_rebalance + total_in_usd

        amount_cad_to_usd_conversion = .0
        for ticker, position in positions.items():
            if ticker in counterpart_tickers:
                continue

            if ticker in counterparts and PREFER_COUNTERPARTS:
                counterpart = positions[counterparts[ticker]]

                position.sum_to_rebalance = (
                    total_with_rebalance * position.percent_ideal
                    - position.quantity * position.price_in_usd
                    - counterpart.quantity * counterpart.price_in_usd
                )

                print("Sum to rebalance: ", position.sum_to_rebalance)

                counterpart.quantity_to_rebalance = int(position.sum_to_rebalance / counterpart.price_in_usd)
                percent_real = (
                    position.price_in_usd * position.quantity + counterpart.price_in_usd * (
                        counterpart.quantity_to_rebalance + counterpart.quantity
                    )
                ) / total_with_rebalance

                print(
                    "How many stock of", counterpart.symbol, "to buy:", counterpart.quantity_to_rebalance,
                    ". Price:", round(counterpart.price_in_usd, 4),
                    "Real percent:", round(percent_real, 4), "\n"
                )
            else:
                position.sum_to_rebalance = (
                    total_with_rebalance * position.percent_ideal - position.quantity * position.price_in_usd
                )

                print("Sum to rebalance: ", position.sum_to_rebalance)
                
                position.quantity_to_rebalance = int(position.sum_to_rebalance / position.price_in_usd)

                if position.currency == "CAD":
                    amount_cad_to_usd_conversion += position.sum_to_rebalance
                position.percent_real = (
                    position.price_in_usd * (position.quantity + position.quantity_to_rebalance)
                        / total_with_rebalance
                )

                print(
                    "How many stock of", position.symbol, "to buy:", position.quantity_to_rebalance,
                    ". Price:", round(position.price_in_usd, 4),
                    "Real percent:", round(position.percent_real, 4), "\n"
                )

        print(
            "Total cash: USD", round(total_in_usd, 4),
            "CAD:", round(total_in_cad, 4),
            "CAD-USD:", round(total_cad_to_usd, 4), "\n"
        )
        print("Total cash with rebalance", total_with_rebalance, "\n")
        print("How much to rebalance:", cash_to_rebalance, "\n")
        print("Amount of USD to convert to CAD:", amount_cad_to_usd_conversion, "\n")


asyncio.run(main())
