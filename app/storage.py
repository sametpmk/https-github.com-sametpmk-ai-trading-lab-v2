from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os, csv

class Storage:
    def __init__(self, sqlite_path: str):
        os.makedirs("data/csv", exist_ok=True)
        self.engine = create_engine(f"sqlite:///{sqlite_path}", echo=False, future=True)
        self.meta = MetaData()
        self.trades = Table("trades", self.meta,
            Column("id", Integer, primary_key=True),
            Column("batch_id", String),
            Column("strategy_id", String),
            Column("symbol", String),
            Column("ts_open", DateTime),
            Column("ts_close", DateTime),
            Column("side", String),
            Column("entry", Float),
            Column("exit", Float),
            Column("pnl", Float),
            Column("extra", JSON, nullable=True),
        )
        self.meta.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def log_trade(self, batch_id: str, strategy_id: str, symbol: str, ts_open, ts_close, side: str, entry: float, exit_: float, pnl: float, extra=None):
        with self.engine.begin() as conn:
            conn.execute(self.trades.insert().values(
                batch_id=batch_id, strategy_id=strategy_id, symbol=symbol,
                ts_open=ts_open, ts_close=ts_close, side=side,
                entry=entry, exit=exit_, pnl=pnl, extra=extra
            ))
        folder = f"data/csv/{batch_id}"
        os.makedirs(folder, exist_ok=True)
        path = f"{folder}/{strategy_id}_{symbol}.csv"
        new = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            import csv as _csv
            w = _csv.writer(f)
            if new:
                w.writerow(["batch_id","strategy_id","symbol","ts_open","ts_close","side","entry","exit","pnl"])
            w.writerow([batch_id, strategy_id, symbol, ts_open.isoformat(), ts_close.isoformat(), side, entry, exit_, pnl])
