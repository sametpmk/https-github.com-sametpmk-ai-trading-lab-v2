import itertools, random
from .rsi_ema import RSI_EMA
from .macd_bb import MACD_BB
class StrategyRegistry:
    def __init__(self, seed=42, timeframes=None):
        random.seed(seed)
        self.timeframes = timeframes or ["15m"]
        self.rsi_ema_grid = list(itertools.product([14,21,28,35],[25,30,35],[65,70,75],[20,50,100,200],[50,100,200,300]))
        self.macd_bb_grid = list(itertools.product([8,12],[17,26],[5,9],[14,20],[1.5,2.0,2.5]))
        self.catalog = []
        sid = 0
        for tf in self.timeframes:
            for p in self.rsi_ema_grid:
                rid = f"RSIEMA_{sid:05d}_{tf}"
                self.catalog.append({"id": rid, "type": "RSI_EMA", "timeframe": tf,
                                     "params": {"rsi_len": p[0], "rsi_buy": p[1], "rsi_sell": p[2], "ema_fast": p[3], "ema_slow": p[4]}})
                sid += 1
            for p in self.macd_bb_grid:
                mid = f"MACDBB_{sid:05d}_{tf}"
                self.catalog.append({"id": mid, "type": "MACD_BB", "timeframe": tf,
                                     "params": {"macd_fast": p[0], "macd_slow": p[1], "macd_signal": p[2], "bb_len": p[3], "bb_mult": p[4]}})
                sid += 1
    def grids(self):
        return {"RSI_EMA": self.rsi_ema_grid, "MACD_BB": self.macd_bb_grid}
    def pick_n(self, batch_id: str, n: int):
        random.seed(hash(batch_id) & 0xffffffff)
        return random.sample(self.catalog, n)
    def instantiate(self, sdef):
        return RSI_EMA(sdef["id"], timeframe=sdef.get("timeframe"), **sdef["params"]) if sdef["type"]=="RSI_EMA" else MACD_BB(sdef["id"], timeframe=sdef.get("timeframe"), **sdef["params"])
    def add_generated(self, items):
        start = len(self.catalog)
        for i, it in enumerate(items):
            nid = f"{it['type']}_G{start+i:05d}_{it.get('timeframe','15m')}"
            self.catalog.append({"id": nid, **it})
