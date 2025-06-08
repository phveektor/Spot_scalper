import typer
from loguru import logger
from dotenv import load_dotenv
import os

app = typer.Typer()

load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

@app.command()
def run(
    mode: str = typer.Option("dry-run", help="Mode: dry-run or live"),
    strategy: str = typer.Option("ema_scalper", help="Strategy to use"),
    symbol: str = typer.Option("BTC/USDT", help="Trading pair symbol"),
    timeframe: str = typer.Option("1m", help="Candlestick timeframe"),
    backtest: bool = typer.Option(False, help="Run backtest instead of live trading")
):
    logger.info(f"Starting Spot Scalper Bot in {mode} mode with {strategy} strategy.")
    if backtest:
        from backtest.backtest_runner import run_backtest
        run_backtest(strategy, symbol, timeframe)
    else:
        # Import and run the trading loop
        from strategies.ema_scalper import run_strategy
        run_strategy(symbol, timeframe, mode)

if __name__ == "__main__":
    app() 