from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
import ccxt
from typing import Dict, List
import os
from dotenv import load_dotenv
from strategies.ema_scalper import EMARSIScalper, StrategyConfig

load_dotenv()

class BacktestRunner:
    def __init__(self, strategy_config: StrategyConfig = None):
        self.strategy = EMARSIScalper(strategy_config)
        self.exchange = ccxt.bybit({
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
            'enableRateLimit': True
        })
        self.results = {
            'trades': [],
            'metrics': {}
        }

    def fetch_historical_data(self, symbol: str, timeframe: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical OHLCV data for backtesting."""
        logger.info(f"Fetching {days} days of historical data for {symbol}")
        
        # Calculate start time
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Fetch data
        ohlcv = self.exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=int(start_time.timestamp() * 1000),
            limit=1000
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df

    def run_backtest(self, symbol: str, timeframe: str, initial_balance: float = 1000.0) -> Dict:
        """Run backtest on historical data."""
        logger.info(f"Starting backtest for {symbol} on {timeframe} timeframe")
        
        # Fetch historical data
        df = self.fetch_historical_data(symbol, timeframe)
        
        # Calculate indicators
        df = self.strategy.calculate_indicators(df)
        
        # Initialize backtest variables
        balance = initial_balance
        position = None
        trades = []
        
        # Iterate through each candle
        for i in range(len(df)):
            current_data = df.iloc[:i+1]
            current_price = current_data.iloc[-1]['close']
            
            # Check for entry
            if not position:
                should_enter, reason = self.strategy.should_enter(current_data)
                if should_enter:
                    position_size = self.strategy.calculate_position_size(balance, current_price)
                    position = {
                        'entry_price': current_price,
                        'amount': position_size,
                        'entry_time': current_data.iloc[-1]['timestamp']
                    }
                    balance -= position_size * current_price
                    logger.info(f"Backtest Entry: {reason} at {current_price}")
            
            # Check for exit
            elif position:
                should_exit, reason = self.strategy.should_exit(current_data, position['entry_price'])
                if should_exit:
                    exit_value = position['amount'] * current_price
                    pnl = exit_value - (position['amount'] * position['entry_price'])
                    balance += exit_value
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': current_data.iloc[-1]['timestamp'],
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'amount': position['amount'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / (position['amount'] * position['entry_price'])) * 100,
                        'reason': reason
                    })
                    
                    logger.info(f"Backtest Exit: {reason} at {current_price}")
                    position = None
        
        # Calculate metrics
        self.calculate_metrics(trades, initial_balance)
        
        return self.results

    def calculate_metrics(self, trades: List[Dict], initial_balance: float):
        """Calculate and store backtest performance metrics."""
        if not trades:
            logger.warning("No trades executed during backtest")
            return
        
        # Convert trades to DataFrame
        trades_df = pd.DataFrame(trades)
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        win_rate = (winning_trades / total_trades) * 100
        
        total_pnl = trades_df['pnl'].sum()
        total_pnl_pct = (total_pnl / initial_balance) * 100
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if (total_trades - winning_trades) > 0 else 0
        
        max_drawdown = self.calculate_max_drawdown(trades_df)
        
        # Store results
        self.results['trades'] = trades
        self.results['metrics'] = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'max_drawdown_pct': max_drawdown,
            'final_balance': initial_balance + total_pnl
        }
        
        # Log results
        logger.info("\nBacktest Results:")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Total PnL: {total_pnl_pct:.2f}%")
        logger.info(f"Average Win: {avg_win:.2f}%")
        logger.info(f"Average Loss: {avg_loss:.2f}%")
        logger.info(f"Max Drawdown: {max_drawdown:.2f}%")
        logger.info(f"Final Balance: ${self.results['metrics']['final_balance']:.2f}")

    def calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown from trade history."""
        if trades_df.empty:
            return 0.0
            
        # Calculate cumulative returns
        cumulative_returns = (1 + trades_df['pnl_pct'] / 100).cumprod()
        
        # Calculate running maximum
        running_max = cumulative_returns.cummax()
        
        # Calculate drawdowns
        drawdowns = (cumulative_returns - running_max) / running_max * 100
        
        return abs(drawdowns.min())

def run_backtest(strategy_name: str, symbol: str, timeframe: str):
    """Entry point for backtesting."""
    logger.info(f"Running backtest for {strategy_name} on {symbol} ({timeframe})")
    
    # Create backtest runner
    runner = BacktestRunner()
    
    # Run backtest
    results = runner.run_backtest(symbol, timeframe)
    
    return results 