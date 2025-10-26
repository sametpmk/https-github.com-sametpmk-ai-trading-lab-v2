import numpy as np
class RSI_EMA:
    def __init__(self, sid: str, rsi_len=14, rsi_buy=30, rsi_sell=70, ema_fast=20, ema_slow=50, timeframe="15m"):
        self.sid=sid; self.rsi_len=rsi_len; self.rsi_buy=rsi_buy; self.rsi_sell=rsi_sell; self.ema_fast=ema_fast; self.ema_slow=ema_slow; self.tf=timeframe
    def strategy_id(self): return self.sid
    def timeframe(self): return self.tf
    def _ema(self, arr, n):
        k=2/(n+1); ema=[arr[0]]
        for x in arr[1:]: ema.append(ema[-1]+k*(x-ema[-1]))
        return np.array(ema)
    def _rsi(self, arr, n):
        deltas=np.diff(arr); ups=np.where(deltas>0,deltas,0.0); downs=np.where(deltas<0,-deltas,0.0)
        roll_up=np.convolve(ups,np.ones(n)/n,mode='valid'); roll_down=np.convolve(downs,np.ones(n)/n,mode='valid')
        rs=roll_up/(roll_down+1e-9); rsi=100-(100/(1+rs)); pad=[50.0]*(len(arr)-len(rsi))
        return np.array(pad + rsi.tolist())
    def generate_signal(self, candles):
        closes=np.array([c["close"] for c in candles], dtype=float)
        if len(closes) < max(self.ema_slow, self.rsi_len)+5: return None
        ema_f=self._ema(closes,self.ema_fast); ema_s=self._ema(closes,self.ema_slow)
        rsi=self._rsi(closes,self.rsi_len)
        if ema_f[-1]>ema_s[-1] and rsi[-1]<=self.rsi_buy: return "BUY"
        if ema_f[-1]<ema_s[-1] and rsi[-1]>=self.rsi_sell: return "SELL"
        if abs(closes[-1]-ema_s[-1]) / max(1e-9, ema_s[-1]) < 0.001: return "EXIT"
        return None
