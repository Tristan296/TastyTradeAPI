import time
from main import *
from tastytrade.order import NewOrder, OrderAction, OrderTimeInForce, OrderType
from http.client import HTTPException as HTTPError

import asyncio

def calculate_iv_rank(current_iv, iv_history):
    iv_high = max(iv_history)
    iv_low = min(iv_history)
    if iv_high == iv_low:
        return 0
    return ((current_iv - iv_low) / (iv_high - iv_low)) * 100

async def get_option_quote(session, symbol, expiration, strike, option_type):
        # Fetch the latest quote for the option contract
        response = await session.get(
            f'https://api.tastytrade.com/v1/marketdata/option-chains/{symbol}/options'
        )
        if response.status != 200:
            raise ValueError(f"Failed to fetch option quote: {response.status}")
        options = await response.json()

        # Find the specific option contract
        for option in options['data']['items']:
            if (
                option['expiration-date'] == expiration
                and option['strike-price'] == strike
                and option['option-type'] == option_type
            ):
                return option

        raise KeyError("Option contract not found")


async def smart_price_option_order(
        session, symbol, expiration, strike, option_type, quantity, side, max_attempts=5, delay=2
    ):
        for attempt in range(max_attempts):
            # Fetch current market data for the option
            option_quote = await get_option_quote(session, symbol, expiration, strike, option_type)
            mid_price = (option_quote['bid-price'] + option_quote['ask-price']) / 2

            # Adjust price based on attempt
            price_adjustment = (attempt / max_attempts) * (option_quote['ask-price'] - option_quote['bid-price'])
            if side == 'buy':
                price = mid_price + price_adjustment
            else:
                price = mid_price - price_adjustment

            # Place limit order for the option
            order = await place_limit_order(session, symbol, quantity, side, price, expiration, strike, option_type)

            # Wait for order to fill
            filled = await wait_for_fill(session, order['id'], timeout=delay)
            if filled:
                return order

        # If not filled, place market order as fallback
        # return await place_market_order(session, symbol, quantity, side, expiration, strike, option_type)


async def place_limit_order(session, symbol, quantity, side, price, expiration, strike, option_type):
    order = {
        'symbol': symbol,
        'quantity': quantity,
        'side': side,
        'price': price,
        'expiration': expiration,
        'strike': strike,
        'option_type': option_type,
        'order_type': OrderType.LIMIT,
        'time_in_force': OrderTimeInForce.DAY
    }
    response = await session.post('https://api.tastytrade.com/v1/orders', json=order)
    if response.status != 201:
        raise HTTPError(f"Failed to place order: {response.status}")
    return await response.json()

async def wait_for_fill(session, order_id, timeout=60):
    start_time = time.time()
    while True:
        response = await session.get(f'https://api.tastytrade.com/v1/orders/{order_id}')
        if response.status != 200:
            raise HTTPError(f"Failed to fetch order status: {response.status}")
        order_status = await response.json()
        if order_status['status'] == 'FILLED':
            return True
        if time.time() - start_time > timeout:
            return False
        await asyncio.sleep(1)


async def place_market_order(session, symbol, quantity, side, expiration, strike, option_type):
    order = {
        'symbol': symbol,
        'quantity': quantity,
        'side': side,
        'expiration': expiration,
        'strike': strike,
        'option_type': option_type,
        'order_type': OrderType.MARKET,
        'time_in_force': OrderTimeInForce.DAY
    }
    response = await session.post('https://api.tastytrade.com/v1/orders', json=order)
    if response.status != 201:
        raise HTTPError(f"Failed to place order: {response.status}")
    return await response.json()

