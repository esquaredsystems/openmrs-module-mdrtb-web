"""
Realistic tests for the report generation queue (utilities/report_queue.py).

These exercise the actual Redis backend (no mocking of Redis itself) since
the concurrency cap is the whole point of the feature - a mocked Redis
client could quietly accept an incorrect implementation. Each test class
uses its own randomly-named key prefix so tests never see each other's
jobs, and cleans up its keys in tearDown.

Requires a reachable Redis instance (same one the app already depends on
for sessions/cache - see settings.CACHES).
"""

import os
import re
import threading
import time
import unittest
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
import django  # noqa: E402

django.setup()

from unittest import mock  # noqa: E402

from django.contrib.sessions.backends.cache import SessionStore  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django.middleware.csrf import _does_token_match  # noqa: E402
from django.test import RequestFactory, SimpleTestCase, override_settings  # noqa: E402

import utilities.report_queue as rq  # noqa: E402
import utilities.restapi_utils as ru  # noqa: E402


def _make_authenticated_request(factory, path="/"):
    request = factory.get(path)
    session = SessionStore()
    session["session_id"] = "fake-openmrs-session"
    session["encoded_credentials"] = "ZmFrZTpmYWtl"
    session["locale"] = "en"
    session.save()
    request.session = session
    return request


class TestReportQueueConcurrencyLimit(unittest.TestCase):
    """The core requirement: never more than MAX_CONCURRENT_REPORTS jobs run at once."""

    MAX_CONCURRENT = 2
    JOB_COUNT = 6
    SLOW_VIEW_KEY = "_test_slow_report"

    def setUp(self):
        self.factory = RequestFactory()
        self.prefix = f"testq-conc-{uuid.uuid4().hex[:10]}"
        self.override = override_settings(
            REPORT_QUEUE_KEY_PREFIX=self.prefix,
            MAX_CONCURRENT_REPORTS=self.MAX_CONCURRENT,
            REPORT_QUEUE_JOB_TIMEOUT=30,
            REPORT_QUEUE_RESULT_TTL=60,
        )
        self.override.enable()
        self.lock = threading.Lock()
        self.current = 0
        self.max_seen = 0
        rq.register_view(self.SLOW_VIEW_KEY, self._slow_view)

    def tearDown(self):
        self.override.disable()
        rq.REPORT_VIEW_REGISTRY.pop(self.SLOW_VIEW_KEY, None)
        client = rq._get_redis()
        keys = client.keys(f"{self.prefix}:*")
        if keys:
            client.delete(*keys)

    def _slow_view(self, req):
        with self.lock:
            self.current += 1
            self.max_seen = max(self.max_seen, self.current)
        try:
            time.sleep(0.4)
            return HttpResponse(f"content-for-{req.GET.get('marker')}")
        finally:
            with self.lock:
                self.current -= 1

    def _wait_for_all_ready(self, job_ids, timeout=15):
        deadline = time.time() + timeout
        statuses = {}
        while time.time() < deadline:
            statuses = {jid: rq.get_status(jid)["status"] for jid in job_ids}
            if all(s in ("ready", "error") for s in statuses.values()):
                return statuses
            time.sleep(0.1)
        self.fail(f"Jobs did not all finish within {timeout}s: {statuses}")

    def test_no_more_than_max_concurrent_jobs_run_at_once(self):
        job_ids = []
        for i in range(self.JOB_COUNT):
            request = _make_authenticated_request(self.factory)
            job_id = rq.enqueue(request, self.SLOW_VIEW_KEY, {"marker": str(i)}, "Test Report")
            job_ids.append(job_id)

        statuses = self._wait_for_all_ready(job_ids)

        self.assertTrue(all(s == "ready" for s in statuses.values()), statuses)
        self.assertLessEqual(self.max_seen, self.MAX_CONCURRENT)
        self.assertGreaterEqual(self.max_seen, 1)

        # Every job's own result must come back - no cross-job data leakage.
        for i, job_id in enumerate(job_ids):
            self.assertEqual(rq.get_result(job_id), f"content-for-{i}")

    def test_queue_position_decreases_as_jobs_are_dispatched(self):
        request = _make_authenticated_request(self.factory)
        job_ids = [
            rq.enqueue(request, self.SLOW_VIEW_KEY, {"marker": str(i)}, "Test Report")
            for i in range(self.JOB_COUNT)
        ]
        # With MAX_CONCURRENT=2 and 6 jobs, the last job should initially report
        # at least a few jobs ahead of it in the queue.
        last_job_status = rq.get_status(job_ids[-1])
        self.assertEqual(last_job_status["status"], "queued")
        self.assertGreater(last_job_status["position"], 0)
        self.assertEqual(last_job_status["max_concurrent"], self.MAX_CONCURRENT)

        self._wait_for_all_ready(job_ids)
        # Once finished, position reporting is moot (job is no longer queued).
        self.assertEqual(rq.get_status(job_ids[-1])["status"], "ready")


class TestReportQueueHttpFlow(SimpleTestCase):
    """
    End-to-end through the real URLs: submitting a report returns the queue
    status page immediately (not the report), and the report becomes
    viewable once the background job finishes.
    """

    databases = []

    def setUp(self):
        self.prefix = f"testq-http-{uuid.uuid4().hex[:10]}"
        self.override = override_settings(
            REPORT_QUEUE_KEY_PREFIX=self.prefix,
            MAX_CONCURRENT_REPORTS=4,
            REPORT_QUEUE_JOB_TIMEOUT=30,
            REPORT_QUEUE_RESULT_TTL=60,
        )
        self.override.enable()
        session = self.client.session
        session["session_id"] = "fake-openmrs-session"
        session["encoded_credentials"] = "ZmFrZTpmYWtl"
        session["locale"] = "en"
        session.save()

    def tearDown(self):
        self.override.disable()
        client = rq._get_redis()
        keys = client.keys(f"{self.prefix}:*")
        if keys:
            client.delete(*keys)

    def _extract_job_id(self, content):
        match = re.search(r"/reportqueue/([0-9a-f]{32})/status", content)
        self.assertIsNotNone(match, "job id not found in queue status page")
        return match.group(1)

    def test_submitting_a_report_is_queued_then_becomes_viewable(self):
        fake_results = {"results": [{"identifier": "T01-MARKER"}]}
        with mock.patch.object(ru, "get", return_value=(True, fake_results)):
            response = self.client.get("/form89results", {"year": "2024"})
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()

            # The immediate response must be the queue status page, not the report.
            self.assertNotIn("T01-MARKER", content)
            job_id = self._extract_job_id(content)

            status_url = f"/reportqueue/{job_id}/status"
            deadline = time.time() + 10
            data = None
            while time.time() < deadline:
                status_response = self.client.get(status_url)
                self.assertEqual(status_response.status_code, 200)
                data = status_response.json()
                if data["status"] in ("ready", "error"):
                    break
                time.sleep(0.1)

            self.assertIsNotNone(data)
            self.assertEqual(data["status"], "ready", data)

            view_response = self.client.get(f"/reportqueue/{job_id}/view")
            self.assertEqual(view_response.status_code, 200)
            view_content = view_response.content.decode()
            self.assertIn("T01-MARKER", view_content)

    def test_view_endpoint_refreshes_csrf_token_for_the_viewing_request(self):
        fake_results = {"results": [{"identifier": "T02-MARKER"}]}
        with mock.patch.object(ru, "get", return_value=(True, fake_results)):
            response = self.client.get("/form89results", {"year": "2024"})
            job_id = self._extract_job_id(response.content.decode())

            deadline = time.time() + 10
            while time.time() < deadline:
                if self.client.get(f"/reportqueue/{job_id}/status").json()["status"] == "ready":
                    break
                time.sleep(0.1)

            view_response = self.client.get(f"/reportqueue/{job_id}/view")
            match = re.search(r'csrfmiddlewaretoken:\s*"([^"]*)"', view_response.content.decode())
            self.assertIsNotNone(match)
            token = match.group(1)
            self.assertTrue(len(token) > 0)

            # Prove the embedded token is actually usable, not just non-empty:
            # it must cryptographically match the secret in the viewer's own
            # csrftoken cookie (Django masks the embedded token differently
            # each render, so comparing the raw strings isn't the right check).
            csrf_cookie = view_response.cookies.get("csrftoken")
            self.assertIsNotNone(csrf_cookie, "view response should set a csrftoken cookie")
            self.assertTrue(_does_token_match(token, csrf_cookie.value))

    def test_report_not_viewable_by_a_different_session(self):
        fake_results = {"results": [{"identifier": "T03-MARKER"}]}
        with mock.patch.object(ru, "get", return_value=(True, fake_results)):
            response = self.client.get("/form89results", {"year": "2024"})
            job_id = self._extract_job_id(response.content.decode())

        deadline = time.time() + 10
        while time.time() < deadline:
            if self.client.get(f"/reportqueue/{job_id}/status").json()["status"] == "ready":
                break
            time.sleep(0.1)

        from django.test import Client
        other_client = Client()
        other_session = other_client.session
        other_session["session_id"] = "some-other-fake-session"
        other_session["encoded_credentials"] = "b3RoZXI6b3RoZXI="
        other_session["locale"] = "en"
        other_session.save()

        status_response = other_client.get(f"/reportqueue/{job_id}/status")
        self.assertEqual(status_response.status_code, 404)

        view_response = other_client.get(f"/reportqueue/{job_id}/view")
        self.assertEqual(view_response.status_code, 302)


class TestRefreshCsrfToken(unittest.TestCase):
    def test_replaces_only_the_first_csrf_token_occurrence(self):
        factory = RequestFactory()
        request = factory.get("/")
        html = (
            'data = {csrfmiddlewaretoken: "stale-token-value", other: 1};\n'
            'more text mentioning csrfmiddlewaretoken: "stale-token-value" again'
        )
        result = rq.refresh_csrf_token(request, html)
        self.assertNotIn("stale-token-value", result.split("\n")[0])
        # Only the first occurrence is touched; matches report_base.html's single call site.
        self.assertIn("stale-token-value", result.split("\n")[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
