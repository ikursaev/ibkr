import aiohttp
import asyncio
import dataclasses as dc


ideal = {
    "XIC": 30,
    "VUN": 30,
    "AVUV": 10,
    "XEF": 16,
    "AVDV": 6,
    "XEC": 8,
}


@dc.dataclass
class Position:
    symbol: str
    price: float
    value: float
    exchange_rate: float
    price_in_usd: float
    currency: str
    quantity: int
    value_in_usd: float = .0
    percent_from_total: float = .0
    percent_ideal: float = .0
    percent_real: float = .0
    percent_delta: float = .0
    sum_to_rebalance: float = .0
    quantity_to_rebalance: int = 0

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


positions: list[Position] = []


async def main():
    async with aiohttp.ClientSession(uri, connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        account_id = await get_account_id(session)
        cash = await get_cash(session, account_id)
        portfolio = await get_portfolio(session, account_id)

        total_in_usd = .0
        total_in_cad = .0
        total_cad_to_usd = .0

        for asset in portfolio:
            currency = asset["currency"]
            exchange_rate = cash[currency]["exchangerate"]

            value = asset["mktValue"]

            value_in_usd = exchange_rate * asset["mktValue"]
            price_in_usd = exchange_rate * asset["mktPrice"]

            positions.append(Position(
                asset["ticker"],
                asset["mktPrice"],
                value,
                exchange_rate,
                price_in_usd,
                asset["currency"],
                int(asset["position"]),
                value_in_usd=value_in_usd,
                percent_ideal=ideal.get(asset["ticker"], .0)
            ))

            total_in_usd += value_in_usd

            if currency == "CAD":
                total_in_cad += value
                total_cad_to_usd += value * exchange_rate

        for position in positions:
            position.percent_from_total = position.value_in_usd / total_in_usd * 100
            position.percent_delta = position.percent_ideal - position.percent_from_total

        cash_to_rebalance = .0
        for currency, value in cash.items():
            if currency == "BASE":
                cash_to_rebalance = value["settledcash"]

        total_with_rebalance = cash_to_rebalance + total_in_usd

        amount_cad_to_usd_conversion = .0
        for position in positions:
            position.sum_to_rebalance = total_with_rebalance * (position.percent_ideal / 100) - position.value_in_usd
            position.quantity_to_rebalance = int(position.sum_to_rebalance / position.price_in_usd)
            if position.currency == "CAD":
                amount_cad_to_usd_conversion += position.sum_to_rebalance

            position.percent_real = (position.price_in_usd * (position.quantity + position.quantity_to_rebalance)/total_with_rebalance) * 100

            print(position)

        print("Total cash sum: ", total_in_usd, "\n")
        print("Total cash in CAD: ", total_in_cad, "\n")
        print("Total CAD to USD: ", total_cad_to_usd, "\n")

        print("Total cash with rebalance", total_with_rebalance, "\n")
        print("How much to rebalance: ", cash_to_rebalance, "\n")

        print("Amount of USD to convert to CAD: ", amount_cad_to_usd_conversion, "\n")

        print("How many stocks should I buy to rebalance the portfolio: ")
        for position in positions:
            print(position.symbol, position.quantity_to_rebalance)

asyncio.run(main())
