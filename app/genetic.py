import random, copy
class GeneticOptimizer:
    def __init__(self, timeframes):
        self.timeframes = timeframes
    def crossover(self, p1: dict, p2: dict) -> dict:
        child = {"type": p1["type"], "params": {}, "timeframe": random.choice([p1.get("timeframe"), p2.get("timeframe")])}
        keys = ["rsi_len","rsi_buy","rsi_sell","ema_fast","ema_slow"] if p1["type"]=="RSI_EMA" else ["macd_fast","macd_slow","macd_signal","bb_len","bb_mult"]
        for k in keys: child["params"][k] = random.choice([p1["params"][k], p2["params"][k]])
        return child
    def mutate(self, s: dict, grids: dict, rate: float = 0.3) -> dict:
        out = copy.deepcopy(s)
        import random as _r
        if _r.random() < 0.5:
            out["timeframe"] = _r.choice(self.timeframes)
        if _r.random() < rate:
            if s["type"] == "RSI_EMA":
                grid = grids["RSI_EMA"]; pick = _r.choice(["rsi_len","rsi_buy","rsi_sell","ema_fast","ema_slow"])
            else:
                grid = grids["MACD_BB"]; pick = _r.choice(["macd_fast","macd_slow","macd_signal","bb_len","bb_mult"])
            def grid_options(grid_list, key):
                key_idx = {"rsi_len":0,"rsi_buy":1,"rsi_sell":2,"ema_fast":3,"ema_slow":4,"macd_fast":0,"macd_slow":1,"macd_signal":2,"bb_len":3,"bb_mult":4}[key]
                return sorted({row[key_idx] for row in grid_list})
            out["params"][pick] = _r.choice(list(grid_options(grid, pick)))
        return out
