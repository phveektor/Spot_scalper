# Spot Scalper Bot

A lightweight, containerized Python-based spot trading scalping bot using Bybit's official API. The bot supports both live trading and historical backtesting using Bybit spot data.

## Features

- 🚀 Real-time spot trading on Bybit
- 📊 Historical data backtesting
- 🔄 EMA-based scalping strategy
- 📈 PnL tracking and logging
- 🐳 Docker containerization
- ☁️ Render deployment support
- 🔧 Configurable trading parameters
- 📝 Clean logging with loguru

## Prerequisites

- Python 3.11+
- Docker (optional, for containerization)
- Bybit API credentials
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spot-scalper-bot.git
cd spot-scalper-bot
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
```

## Usage

### Running Locally

1. Dry-run mode (simulated trading):
```bash
python main.py run --mode dry-run --symbol BTC/USDT --timeframe 1m
```

2. Live trading mode:
```bash
python main.py run --mode live --symbol BTC/USDT --timeframe 1m
```

3. Backtesting mode:
```bash
python main.py run --backtest --symbol BTC/USDT --timeframe 1m
```

### Docker Usage

1. Build the Docker image:
```bash
docker build -t spot-scalper .
```

2. Run in dry-run mode:
```bash
docker run -it --env-file .env spot-scalper run --mode dry-run --symbol BTC/USDT --timeframe 1m
```

### Render Deployment

1. Push your code to a Git repository
2. Connect your repository to Render
3. Add your environment variables in Render's dashboard:
   - `BYBIT_API_KEY`
   - `BYBIT_API_SECRET`
4. Deploy using the `render.yaml` configuration

## Project Structure

```
spot_scalper_bot/
├── main.py              # CLI entry point
├── strategies/          # Trading strategies
│   └── ema_scalper.py  # EMA-based scalping strategy
├── backtest/           # Backtesting engine
│   └── backtest_runner.py
├── data/               # Data storage
├── utils/              # Utility functions
│   └── fetch_data.py   # OHLCV data fetcher
├── .env               # Environment variables (create from .env.example)
├── requirements.txt   # Python dependencies
├── Dockerfile        # Docker configuration
└── render.yaml       # Render deployment config
```

## Configuration

The bot can be configured through command-line arguments:

- `--mode`: Trading mode (dry-run/live)
- `--strategy`: Strategy to use (default: ema_scalper)
- `--symbol`: Trading pair (default: BTC/USDT)
- `--timeframe`: Candlestick timeframe (default: 1m)
- `--backtest`: Enable backtesting mode

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

## Support

If you find this project helpful, please give it a ⭐️ on GitHub! 