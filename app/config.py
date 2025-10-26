import yaml, os
def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if os.getenv("TIMEFRAME"):
        cfg["default_timeframe"] = os.getenv("TIMEFRAME")
    if os.getenv("EXCHANGE"):
        cfg["exchange"] = os.getenv("EXCHANGE")
    return cfg
