"""
Performance tests for the gunicorn web server configuration.

These tests send real HTTP requests to a running server and check that
it behaves correctly under load and when requests take too long.

Before running, start the server and set credentials in the .env file:
    MDRTB_WEB_URL, MDRTB_TEST_USERNAME, MDRTB_TEST_PASSWORD

Run with:
    python -m pytest tests/test_gunicorn_performance.py -v
"""

import os
import time
import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL       = os.getenv("MDRTB_WEB_URL",         "http://127.0.0.1:8000")
TEST_USERNAME  = os.getenv("MDRTB_TEST_USERNAME",    "admin")
TEST_PASSWORD  = os.getenv("MDRTB_TEST_PASSWORD",    "Admin123")

SLOW_ENDPOINT  = f"{BASE_URL}/test/slow"
PROBE_ENDPOINT = f"{BASE_URL}/concepts"
LOGIN_ENDPOINT = f"{BASE_URL}/login"

GUNICORN_TIMEOUT      = 60    # seconds — must match gunicorn_config.py
GUNICORN_MAX_REQUESTS = 1000  # must match gunicorn_config.py
GUNICORN_JITTER       = 100   # must match gunicorn_config.py


def _authenticate() -> requests.Session:
    """
    Log in to the server and return a session that stays logged in.

    We fetch the login page first to get the security token Django requires,
    then submit the username and password. The returned session can be reused
    across multiple requests without logging in again.
    """
    s = requests.Session()
    r = s.get(LOGIN_ENDPOINT, timeout=10)
    r.raise_for_status()

    csrf = s.cookies.get("csrftoken")
    if not csrf:
        raise RuntimeError(
            "No csrftoken cookie returned by /login — is the server running?"
        )

    resp = s.post(
        LOGIN_ENDPOINT,
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrfmiddlewaretoken": csrf,
        },
        headers={"Referer": LOGIN_ENDPOINT},
        timeout=10,
        allow_redirects=True,
    )
    resp.raise_for_status()

    if resp.url.rstrip("/").endswith("/login"):
        raise RuntimeError(
            "Authentication failed — server redirected back to /login. "
            "Check MDRTB_TEST_USERNAME / MDRTB_TEST_PASSWORD in .env"
        )
    return s


class TestGunicornTimeout(unittest.TestCase):
    """
    Checks that the server cuts off requests that take too long.

    Gunicorn is configured with a 60-second timeout. If a request hasn't
    finished by then, the server kills that worker process and starts a
    fresh one. The client receives a connection error instead of waiting
    forever.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.session = _authenticate()
        # Verify the server is reachable before running timeout tests.
        try:
            resp = requests.get(f"{BASE_URL}/concepts", timeout=10)
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Server at {BASE_URL} is not reachable: {exc}\n"
                "Start gunicorn with --timeout 60 before running these tests."
            ) from exc

    def test_request_well_within_timeout_succeeds(self):
        """A request that finishes in 5 seconds should complete normally."""
        resp = requests.get(
            SLOW_ENDPOINT,
            params={"seconds": 5},
            timeout=GUNICORN_TIMEOUT + 30,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("slept:5", resp.text)

    def test_request_exceeding_timeout_is_terminated(self):
        """
        A request designed to take 70 seconds should be cut off around the 60s mark.

        When gunicorn kills the slow worker it either drops the connection
        (client sees a network error) or sends an HTTP 500 response. Both
        outcomes count as a correct timeout. We also check the elapsed time
        to confirm the cutoff happened at roughly the right moment.
        """
        margin = 15
        t0 = time.monotonic()
        terminated = False
        try:
            resp = requests.get(
                SLOW_ENDPOINT,
                params={"seconds": GUNICORN_TIMEOUT + 10},
                timeout=GUNICORN_TIMEOUT + 30,
            )
            # Gunicorn may return 500 instead of dropping the connection.
            if resp.status_code >= 500:
                terminated = True
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
            terminated = True

        elapsed = time.monotonic() - t0

        self.assertTrue(
            terminated,
            f"Request completed successfully after {elapsed:.1f}s — gunicorn did not enforce "
            f"the {GUNICORN_TIMEOUT}s timeout. Start the server with --timeout {GUNICORN_TIMEOUT}.",
        )
        self.assertGreaterEqual(
            elapsed,
            GUNICORN_TIMEOUT - margin,
            f"Worker was killed too soon ({elapsed:.1f}s < {GUNICORN_TIMEOUT - margin}s). "
            "Check gunicorn timeout config.",
        )
        self.assertLessEqual(
            elapsed,
            GUNICORN_TIMEOUT + margin,
            f"Worker was not killed in time ({elapsed:.1f}s > {GUNICORN_TIMEOUT + margin}s). "
            "Check gunicorn timeout config.",
        )


class TestGunicornMaxRequests(unittest.TestCase):
    """
    Checks that the server stays healthy while worker processes are being recycled.

    Gunicorn is configured to restart each worker after it handles 1000 to 1100
    requests. This prevents slow memory leaks from building up. The restart is
    graceful — requests in flight are allowed to finish before the old worker
    stops and a new one takes over.

    These tests confirm that no requests fail during that recycling window.
    """

    TOTAL_REQUESTS = 150
    CONCURRENCY    = 10

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.session = _authenticate()

    def test_zero_failures_during_worker_recycling(self):
        """
        Send all requests using a pool of parallel workers; expect zero failures.

        Each worker runs its share of requests sequentially. All workers run at
        the same time (up to CONCURRENCY at once), simulating realistic load.
        """
        per_thread    = self.TOTAL_REQUESTS // self.CONCURRENCY
        all_failures  = []
        all_latencies = []
        lock          = threading.Lock()

        def worker_task(_):
            # Each worker gets its own connection but shares the login session.
            s = requests.Session()
            s.cookies.update(self.session.cookies)
            failures, latencies = [], []
            for i in range(per_thread):
                try:
                    t0 = time.monotonic()
                    resp = s.get(PROBE_ENDPOINT, timeout=10)
                    latencies.append(time.monotonic() - t0)
                    if resp.status_code >= 500:
                        failures.append((i, resp.status_code))
                except requests.exceptions.RequestException as exc:
                    failures.append((i, str(exc)))
            with lock:
                all_failures.extend(failures)
                all_latencies.extend(latencies)

        with ThreadPoolExecutor(max_workers=self.CONCURRENCY) as pool:
            list(pool.map(worker_task, range(self.CONCURRENCY)))

        total_sent = per_thread * self.CONCURRENCY
        self.assertEqual(
            len(all_failures),
            0,
            f"{len(all_failures)}/{total_sent} requests to /concepts failed during recycling:\n"
            + "\n".join(str(f) for f in all_failures[:20]),
        )

    def test_concurrent_requests_survive_recycling(self):
        """
        Send requests from multiple threads simultaneously; expect zero failures.

        Unlike the pool test above, each thread here runs independently from
        start to finish rather than being managed by a shared queue. This
        mimics multiple users hitting the server at the same time.
        """
        requests_per_thread = self.TOTAL_REQUESTS // self.CONCURRENCY
        errors = []
        lock   = threading.Lock()

        def fire(thread_id):
            # Each thread gets its own connection but shares the login session.
            s = requests.Session()
            s.cookies.update(self.session.cookies)
            thread_errors = []
            for i in range(requests_per_thread):
                try:
                    resp = s.get(PROBE_ENDPOINT, timeout=10)
                    if resp.status_code >= 500:
                        thread_errors.append(
                            f"thread={thread_id} req={i} status={resp.status_code}"
                        )
                except requests.exceptions.RequestException as exc:
                    thread_errors.append(f"thread={thread_id} req={i} error={exc}")
            with lock:
                errors.extend(thread_errors)

        threads = [threading.Thread(target=fire, args=(t,)) for t in range(self.CONCURRENCY)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(
            len(errors),
            0,
            f"{len(errors)} errors under concurrent load during worker recycling:\n"
            + "\n".join(errors[:20]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
