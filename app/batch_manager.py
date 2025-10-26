from datetime import datetime, timedelta
class BatchManager:
    def __init__(self, cfg, registry):
        self.cfg = cfg
        self.registry = registry
        self.batch_id = None
        self.started_at = None
        self.ends_at = None
        self.active_strategies = []
    async def ensure_current_batch(self):
        now = datetime.utcnow()
        week_id = now.isocalendar().week
        year = now.isocalendar().year
        desired_id = f"{year}-W{week_id:02d}"
        if self.batch_id != desired_id:
            await self._start_new_batch(desired_id, now)
    def is_rotation_due(self):
        return datetime.utcnow() >= self.ends_at
    async def rotate_batch(self):
        await self.ensure_current_batch()
    async def _start_new_batch(self, batch_id, now):
        duration_days = int(self.cfg.get("batch_duration_days", 7))
        self.batch_id = batch_id
        self.started_at = now
        self.ends_at = now + timedelta(days=duration_days)
        k = int(self.cfg.get("parallel_strategies", 10))
        self.active_strategies = self.registry.pick_n(batch_id, k)
