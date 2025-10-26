from .data_providers.binance_rest import BinanceREST
from .data_providers.binance_ws import BinanceWS
class DataRouter:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.ws = None
        self.rest = BinanceREST(cfg)
        if cfg.get("websockets", False):
            try:
                self.ws = BinanceWS(cfg["symbols"], cfg.get("timeframes", [cfg.get("default_timeframe","15m")]))
                self.ws.start()
            except Exception:
                self.ws = None
    async def fetch(self, symbol: str, timeframe: str, limit: int = 300):
        if self.ws:
            candles = self.ws.get_candles(symbol, timeframe)
            if candles and len(candles) >= min(100, limit//2):
                return candles[-limit:]
        return await self.rest.fetch_ohlcv(symbol, timeframe, limit)
    async def close(self):
        await self.rest.close()
        if self.ws:
            try: self.ws.stop()
            except Exception: pass
