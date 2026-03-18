import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class CacheResultsHelper:
    def __init__(self):
        self.cache_dir = "./tmp/cache/"
        self.cache_duration = timedelta(seconds=int(os.getenv("CACHE_DURATION_SECONDS", 86400)))  # Default cache duration: 24 hours
        self.enabled = os.getenv("CACHE_ENABLED", "false").lower() == "true"

    def is_enabled(self) -> bool:
        return self.enabled

    def read_from_cache(self, analysis_dir: str, simplified: bool) -> tuple[dict | None, str]:
        os.makedirs(self.cache_dir, exist_ok=True)
        safe_analysis_dir = "_".join(Path(analysis_dir).parts)
        if simplified:
            cache_file = os.path.join(self.cache_dir, f"{safe_analysis_dir}-simplified.json")
        else:
            cache_file = os.path.join(self.cache_dir, f"{safe_analysis_dir}.json")
        cache = self._check_cache(cache_file)
        return cache, cache_file


    def _check_cache(self, cache_file: str) -> dict | None:
        if os.path.isfile(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < self.cache_duration:
                with open(cache_file, "r") as f:
                    return json.load(f)
        return None

    def write_to_cache(self, cache_file: str, data: dict):
        with open(cache_file, "w") as f:
            json.dump(data, f)