import logging
import time
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "_logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "results.log"
if LOG_FILE.exists():
    LOG_FILE.unlink()

_LOGGER = logging.getLogger("tests.summary")
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False
if not _LOGGER.handlers:
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(message)s")
    fh.setFormatter(fmt)
    _LOGGER.addHandler(fh)


class CaseLoggerMixin:
    def setUp(self):
        self._t0 = time.perf_counter()
        _LOGGER.info("START %s", self.id())
        super().setUp()

    def tearDown(self):
        status = "OK"
        outcome = getattr(self, "_outcome", None)
        result = getattr(outcome, "result", None) if outcome else None
        if result:
            if any(t is self for t, _ in getattr(result, "failures", [])):
                status = "FAIL"
            elif any(t is self for t, _ in getattr(result, "errors", [])):
                status = "ERROR"
            elif any(t is self for t, _ in getattr(result, "skipped", [])):
                status = "SKIP"
            elif any(t is self for t, _ in getattr(result, "expectedFailures", [])):
                status = "XFAIL"
            elif any(t is self for t in getattr(result, "unexpectedSuccesses", [])):
                status = "XPASS"
        dur_ms = int((time.perf_counter() - getattr(self, "_t0", time.perf_counter())) * 1000)
        _LOGGER.info("%s %s %sms", status, self.id(), dur_ms)
        super().tearDown()


def get_test_logger(module_name: str):
    return _LOGGER
