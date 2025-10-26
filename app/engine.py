import asyncio
from datetime import datetime
from .strategies.registry import StrategyRegistry
from .batch_manager import BatchManager
from .storage import Storage
from .data_router import DataRouter
from .genetic import GeneticOptimizer

class Engine:
    def __init__(self, cfg: dict, storage: Storage):
        self.cfg = cfg
        self.storage = storage
        self.running = False
        self.tasks = []
        self.registry = StrategyRegistry(seed=cfg.get("random_seed", 42), timeframes=cfg.get("timeframes") or [cfg.get("default_timeframe","15m")])
        self.batch = BatchManager(cfg, self.registry)
        self.data = DataRouter(cfg)
        self.loop_delay = int(cfg.get("poll_seconds", 30))
        self.gen = GeneticOptimizer(cfg.get("timeframes") or [cfg.get("default_timeframe","15m")])
    async def start(self):
        self.running = True
        await self.batch.ensure_current_batch()
        for s in self.batch.active_strategies:
            t = asyncio.create_task(self._worker(s))
            self.tasks.append(t)
    async def stop(self):
        self.running = False
        for t in self.tasks: t.cancel()
        self.tasks = []
        await self.data.close()
    async def _worker(self, sdef):
        symbol_list = self.cfg["symbols"]
        strat = self.registry.instantiate(sdef)
        timeframe = sdef.get("timeframe") or self.cfg.get("default_timeframe","15m")
        open_positions = {}
        while self.running:
            if self.batch.is_rotation_due():
                self._evolve_catalog()
                await self.batch.rotate_batch()
                return
            for sym in symbol_list:
                candles = await self.data.fetch(sym, timeframe, self.cfg.get("lookback_candles", 300))
                if not candles or len(candles) < 100: continue
                signal = strat.generate_signal(candles)
                now_price = candles[-1]["close"]
                now_ts = datetime.utcfromtimestamp(candles[-1]["ts"]/1000)
                pos = open_positions.get(sym)
                if signal == "BUY" and pos is None:
                    open_positions[sym] = ("LONG", now_price, now_ts)
                elif signal == "SELL" and pos is None:
                    open_positions[sym] = ("SHORT", now_price, now_ts)
                elif signal == "EXIT" and pos is not None:
                    side, entry, ts_open = pos
                    pnl = (now_price - entry) if side == "LONG" else (entry - now_price)
                    self.storage.log_trade(self.batch.batch_id, strat.strategy_id(), sym, ts_open, now_ts, side, float(entry), float(now_price), float(pnl), extra={"tf": timeframe})
                    open_positions.pop(sym, None)
            await asyncio.sleep(self.loop_delay)
    def _evolve_catalog(self):
        from sqlalchemy import text
        try:
            with self.storage.engine.begin() as conn:
                rs = conn.execute(text("""
                    SELECT strategy_id, SUM(pnl) as total_pnl
                    FROM trades
                    WHERE batch_id = :bid
                    GROUP BY strategy_id
                    ORDER BY total_pnl DESC
                    LIMIT 6
                """), {"bid": self.batch.batch_id}).fetchall()
            if not rs: return
            top_ids = [r[0] for r in rs]
            id2def = {c["id"]: c for c in self.registry.catalog if c["id"] in top_ids}
            seeds = [id2def[i] for i in top_ids if i in id2def]
            children = []
            grids = self.registry.grids()
            for i in range(0, len(seeds)-1, 2):
                c1 = self.gen.crossover(seeds[i], seeds[i+1])
                c2 = self.gen.crossover(seeds[i+1], seeds[i])
                children.extend([self.gen.mutate(c1, grids), self.gen.mutate(c2, grids)])
            if children: self.registry.add_generated(children)
        except Exception:
            pass
    def status_snapshot(self):
        return {
            "running": self.running,
            "batch": {"id": self.batch.batch_id, "started_at": self.batch.started_at.isoformat(), "ends_at": self.batch.ends_at.isoformat()},
            "active_strategies": [s["id"] for s in self.batch.active_strategies],
            "symbols": self.cfg["symbols"],
            "timeframes": self.cfg.get("timeframes") or [self.cfg.get("default_timeframe","15m")],
        }
