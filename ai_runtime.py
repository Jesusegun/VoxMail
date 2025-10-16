import os
import threading

_processor_singleton = None
_processor_lock = threading.RLock()

# Limit concurrent AI-heavy requests across the process (tunable via env)
SEMAPHORE = threading.Semaphore(int(os.environ.get('AI_MAX_CONCURRENCY', '3')))


def get_advanced_processor():
    """Return a process-wide AdvancedEmailProcessor singleton.

    Ensures heavy Transformer models are loaded once per process to avoid
    duplicate memory usage and startup thrash under concurrent load.
    """
    global _processor_singleton
    if _processor_singleton is not None:
        return _processor_singleton

    with _processor_lock:
        if _processor_singleton is None:
            from complete_advanced_ai_processor import AdvancedEmailProcessor
            _processor_singleton = AdvancedEmailProcessor()
        return _processor_singleton


def warmup():
    """Eagerly initialize the singleton to load models at startup."""
    _ = get_advanced_processor()


