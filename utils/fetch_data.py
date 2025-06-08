import ccxt
from loguru import logger
 
def fetch_ohlcv(symbol, timeframe, since=None, limit=1000):
    logger.info(f"Fetching OHLCV for {symbol} ({timeframe})...")
    exchange = ccxt.bybit()
    return exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit) 