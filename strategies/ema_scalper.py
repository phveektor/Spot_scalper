from loguru import logger
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")


def run_strategy(symbol, timeframe, mode):
    logger.info(f"Running EMA Scalper on {symbol} ({timeframe}) in {mode} mode.")
    # TODO: Implement EMA scalping logic
    pass 