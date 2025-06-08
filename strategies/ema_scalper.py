from loguru import logger
import ccxt
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

@dataclass
class StrategyConfig:
    # EMAs
    ema_fast: int = 5
    ema_slow: int = 20
    ema_trend: int = 200
    
    # RSI
    rsi_period: int = 14
    rsi_lower: float = 45
    rsi_upper: float = 65
    
    # Volume
    volume_ma_period: int = 20
    volume_spike_threshold: float = 1.15
    
    # Risk Management
    take_profit_pct: float = 1.5
    stop_loss_pct: float = 0.8
    trailing_stop_pct: float = 0.5
    trailing_stop_activation_pct: float = 1.0
    
    # Position Sizing
    max_position_size: float = 0.1  # 10% of available balance

class EMARSIScalper:
    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()
        self.exchange = ccxt.bybit({
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
            'enableRateLimit': True
        })
        self.current_position = None
        self.trade_history = []
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators needed for the strategy."""
        # EMAs
        df['ema_fast'] = df['close'].ewm(span=self.config.ema_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.config.ema_slow).mean()
        df['ema_trend'] = df['close'].ewm(span=self.config.ema_trend).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume
        df['volume_ma'] = df['volume'].rolling(window=self.config.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def should_enter(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Determine if we should enter a long position."""
        if len(df) < self.config.ema_trend:
            return False, "Insufficient data"
            
        current = df.iloc[-1]
        
        # Trend check
        if current['close'] <= current['ema_trend']:
            return False, "Price below 200 EMA"
            
        # EMA crossover
        if not (df['ema_fast'].iloc[-2] <= df['ema_slow'].iloc[-2] and 
                df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]):
            return False, "No EMA crossover"
            
        # RSI check
        if not (self.config.rsi_lower <= current['rsi'] <= self.config.rsi_upper):
            return False, f"RSI {current['rsi']:.2f} outside range"
            
        # Volume check
        if current['volume_ratio'] < self.config.volume_spike_threshold:
            return False, "No volume spike"
            
        return True, "All conditions met"
    
    def should_exit(self, df: pd.DataFrame, entry_price: float) -> Tuple[bool, str]:
        """Determine if we should exit the current position."""
        if not self.current_position:
            return False, "No position"
            
        current = df.iloc[-1]
        current_price = current['close']
        
        # Calculate PnL
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Take profit
        if pnl_pct >= self.config.take_profit_pct:
            return True, f"Take profit hit: {pnl_pct:.2f}%"
            
        # Stop loss
        if pnl_pct <= -self.config.stop_loss_pct:
            return True, f"Stop loss hit: {pnl_pct:.2f}%"
            
        # Trailing stop
        if pnl_pct >= self.config.trailing_stop_activation_pct:
            trailing_stop_price = entry_price * (1 + (pnl_pct - self.config.trailing_stop_pct) / 100)
            if current_price < trailing_stop_price:
                return True, f"Trailing stop hit: {pnl_pct:.2f}%"
                
        # EMA cross exit
        if (df['ema_fast'].iloc[-2] >= df['ema_slow'].iloc[-2] and 
            df['ema_fast'].iloc[-1] < df['ema_slow'].iloc[-1]):
            return True, "EMA cross exit"
            
        return False, "Holding position"
    
    def calculate_position_size(self, balance: float, current_price: float) -> float:
        """Calculate position size based on risk management rules."""
        return min(balance * self.config.max_position_size, balance)
    
    def execute_trade(self, symbol: str, side: str, amount: float, price: float, mode: str = 'dry-run') -> Dict:
        """Execute a trade (real or simulated)."""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'mode': mode
        }
        
        if mode == 'live':
            try:
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=side,
                    amount=amount,
                    price=price
                )
                trade['order_id'] = order['id']
                logger.info(f"Executed {side} order: {amount} {symbol} at {price}")
            except Exception as e:
                logger.error(f"Trade execution failed: {str(e)}")
                return None
        else:
            logger.info(f"Simulated {side} order: {amount} {symbol} at {price}")
            
        self.trade_history.append(trade)
        return trade
    
    def run_strategy(self, symbol: str, timeframe: str, mode: str = 'dry-run'):
        """Main strategy loop."""
        logger.info(f"Running EMA Scalper on {symbol} ({timeframe}) in {mode} mode.")
        
        while True:
            try:
                # Fetch latest candles
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=300)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Calculate indicators
                df = self.calculate_indicators(df)
                
                # Check for entry/exit
                if not self.current_position:
                    should_enter, reason = self.should_enter(df)
                    if should_enter:
                        balance = float(self.exchange.fetch_balance()['USDT']['free'])
                        position_size = self.calculate_position_size(balance, df['close'].iloc[-1])
                        
                        self.current_position = self.execute_trade(
                            symbol=symbol,
                            side='buy',
                            amount=position_size,
                            price=df['close'].iloc[-1],
                            mode=mode
                        )
                        logger.info(f"Entered position: {reason}")
                else:
                    should_exit, reason = self.should_exit(df, self.current_position['price'])
                    if should_exit:
                        self.execute_trade(
                            symbol=symbol,
                            side='sell',
                            amount=self.current_position['amount'],
                            price=df['close'].iloc[-1],
                            mode=mode
                        )
                        logger.info(f"Exited position: {reason}")
                        self.current_position = None
                
                # Log performance metrics
                if len(self.trade_history) > 0:
                    self.log_performance_metrics()
                
            except Exception as e:
                logger.error(f"Strategy error: {str(e)}")
                continue
    
    def log_performance_metrics(self):
        """Calculate and log performance metrics."""
        if not self.trade_history:
            return
            
        # Calculate metrics
        trades = pd.DataFrame(self.trade_history)
        winning_trades = trades[trades['side'] == 'sell']
        
        if len(winning_trades) > 0:
            win_rate = len(winning_trades) / len(trades) * 100
            avg_roi = winning_trades['price'].pct_change().mean() * 100
            total_pnl = (winning_trades['price'].iloc[-1] - winning_trades['price'].iloc[0]) / winning_trades['price'].iloc[0] * 100
            
            logger.info(f"Performance Metrics:")
            logger.info(f"Win Rate: {win_rate:.2f}%")
            logger.info(f"Average ROI: {avg_roi:.2f}%")
            logger.info(f"Total PnL: {total_pnl:.2f}%")

def run_strategy(symbol: str, timeframe: str, mode: str = 'dry-run'):
    """Entry point for the strategy."""
    strategy = EMARSIScalper()
    strategy.run_strategy(symbol, timeframe, mode) 