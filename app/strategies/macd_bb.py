import numpy as np
class MACD_BB:
    def __init__(self, sid: str, macd_fast=12, macd_slow=26, macd_signal=9, bb_len=20, bb_mult=2.0, timeframe="15m"):
        self.sid=sid; self.macd_fast=macd_fast; self.macd_slow=macd_slow; self.macd_signal=macd_signal; self.bb_len=bb_len; self.bb_mult=bb_mult; self.tf=timeframe
    def strategy_id(self): return self.sid
    def timeframe(self): return self.tf
    def _ema(self, arr, n):
        k=2/(n+1); ema=[arr[0]]
        for x in arr[1:]: ema.append(ema[-1]+k*(x-ema[-1]))
        return np.array(ema)
    def _macd(self, arr):
        ema_f=self._ema(arr,self.macd_fast); ema_s=self._ema(arr,self.macd_slow)
        macd=ema_f-ema_s; signal=self._ema(macd,self.macd_signal); hist=macd-signal
        return macd, signal, hist
    def _bb(self, arr):
        if len(arr)<self.bb_len: return None, None
        w=arr[-self.bb_len:]; m=np.mean(w); s=np.std(w)+1e-9
        return m+self.bb_mult*s, m-self.bb_mult*s
    def generate_signal(self, candles):
        closes=np.array([c["close"] for c in candles], dtype=float)
        if len(closes) < max(self.macd_slow+self.macd_signal, self.bb_len)+5: return None
        _,_,hist=self._macd(closes); upper,lower=self._bb(closes); price=closes[-1]
        if upper is None: return None
        if hist[-1]>0 and price<lower: return "BUY"
        if hist[-1]<0 and price>upper: return "SELL"
        mid=(upper+lower)/2
        if abs(price-mid)/mid < 0.002: return "EXIT"
        return None
