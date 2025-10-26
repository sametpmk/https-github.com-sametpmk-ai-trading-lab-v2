import ccxt.async_support as ccxt, os
def _mk_client(exchange_name: str, api_key: str|None, api_secret: str|None):
    if exchange_name.lower() == "binanceusdm":
        klass = getattr(ccxt, "binanceusdm")
    else:
        klass = getattr(ccxt, "binance")
    return klass({
        "apiKey": api_key or "",
        "secret": api_secret or "",
        "enableRateLimit": True,
        "options": {"adjustForTimeDifference": True},
    })
class BinanceREST:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.primary = cfg.get("exchange", "binanceusdm")
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_sec = os.getenv("BINANCE_API_SECRET")
        self.client_primary = _mk_client(self.primary, self.api_key, self.api_sec)
        self.client_spot = _mk_client("binance", self.api_key, self.api_sec)
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 300):
        for name, client in [(self.primary, self.client_primary), ("binance", self.client_spot)]:
            try:
                o = await client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                if o:
                    return [{"ts": r[0], "open": r[1], "high": r[2], "low": r[3], "close": r[4], "vol": r[5]} for r in o]
            except Exception:
                continue
        return None
    async def close(self):
        try: await self.client_primary.close()
        except Exception: pass
        try: await self.client_spot.close()
        except Exception: pass
