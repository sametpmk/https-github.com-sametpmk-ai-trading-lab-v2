import collections
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
from binance.lib.utils import config_logging
import logging
class CandleCache:
    def __init__(self, maxlen=1000):
        self.data = {}
        self.maxlen = maxlen
    def push(self, sym, tf, k):
        key = (sym, tf)
        dq = self.data.setdefault(key, collections.deque(maxlen=self.maxlen))
        if len(dq)==0 or dq[-1]["ts"] != k["ts"]:
            dq.append(k)
    def get(self, sym, tf):
        return list(self.data.get((sym, tf), []))
class BinanceWS:
    def __init__(self, symbols, timeframes):
        config_logging(logging, logging.INFO)
        self.cache = CandleCache()
        self.uf = UMFuturesWebsocketClient()
        self.running = False
        self.symbols = symbols
        self.timeframes = timeframes
    def _cb(self, msg):
        try:
            if msg.get("e") == "kline":
                k = msg["k"]; sym = msg["s"]; tf = k["i"]
                self.cache.push(sym, tf, {
                    "ts": int(k["t"]),
                    "open": float(k["o"]),
                    "high": float(k["h"]),
                    "low": float(k["l"]),
                    "close": float(k["c"]),
                    "vol": float(k["v"]),
                })
        except Exception: pass
    def start(self):
        if self.running: return
        self.running = True
        for tf in self.timeframes:
            streams = [f"{s.lower()}@kline_{tf}" for s in self.symbols]
            self.uf.start()
            self.uf.kline(id=1, params=streams, callback=self._cb)
    def stop(self):
        try: self.uf.stop()
        except Exception: pass
        self.running = False
    def get_candles(self, sym, timeframe):
        return self.cache.get(sym, timeframe)
