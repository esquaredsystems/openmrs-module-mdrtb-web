"""
Redis-backed FIFO queue that caps how many reports/patient lists can be
generated at the same time (settings.MAX_CONCURRENT_REPORTS).

Report views are heavy synchronous calls to the OpenMRS REST API. If too many
run at once they tie up every gunicorn worker and the site starts throwing
500s. Instead of running a report view directly, the URLconf routes report
"results" endpoints through report_queue_entry (see app/views.py), which:

1. Stores the request's target report + query params + session as a job in
   Redis and appends the job id to a FIFO list.
2. Tries to dispatch it immediately: if fewer than MAX_CONCURRENT_REPORTS
   jobs are currently running, the job is popped and executed in a
   background thread right away; otherwise it waits in the queue.
3. Returns a small "queued" status page immediately, which polls
   /reportqueue/<job_id>/status and enables a "View Report" button once the
   job's rendered HTML is ready.

Dispatch capacity is coordinated through Redis (a sorted set of active job
ids, scored by expiry time) so the limit holds across every gunicorn worker
process, not just within one. Every worker process also runs a lightweight
background poller (started from AppConfig.ready) that promotes queued jobs
as capacity frees up, so progress isn't solely dependent on some other
request happening to trigger it.

A job is executed by calling its registered report view function directly
(see register_view) with a synthetic request carrying the submitter's
Django session, restored from the session key rather than the original
request object, since dispatch may happen in a different process to the
one that enqueued the job.
"""

import json
import logging
import re
import threading
import time
import uuid

import redis
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.cache import SessionStore
from django.middleware.csrf import get_token
from django.test import RequestFactory

logger = logging.getLogger("django")

# Registered by app/views.py: maps a report's URL key (e.g. "tb03results") to
# the view function that actually fetches and renders it.
REPORT_VIEW_REGISTRY = {}

_DISPATCH_LUA = """
local active_key = KEYS[1]
local queue_key = KEYS[2]
local max_concurrent = tonumber(ARGV[1])
local now = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', active_key, '-inf', now)
local active_count = redis.call('ZCARD', active_key)
if active_count < max_concurrent then
    local job_id = redis.call('LPOP', queue_key)
    if job_id then
        redis.call('ZADD', active_key, now + ttl, job_id)
        return job_id
    end
end
return false
"""

_CSRF_JS_PATTERN = re.compile(r'(csrfmiddlewaretoken:\s*")([^"]*)(")')

_request_factory = RequestFactory()

_redis_clients = {}
_dispatch_scripts = {}

_poller_started = False
_poller_lock = threading.Lock()


def register_view(view_key, view_func):
    REPORT_VIEW_REGISTRY[view_key] = view_func


def _redis_url():
    return settings.REPORT_QUEUE_REDIS_URL


def _get_redis():
    url = _redis_url()
    client = _redis_clients.get(url)
    if client is None:
        client = redis.from_url(url, decode_responses=True)
        _redis_clients[url] = client
    return client


def _get_dispatch_script():
    url = _redis_url()
    script = _dispatch_scripts.get(url)
    if script is None:
        script = _get_redis().register_script(_DISPATCH_LUA)
        _dispatch_scripts[url] = script
    return script


def _prefix():
    return settings.REPORT_QUEUE_KEY_PREFIX


def _queue_key():
    return f"{_prefix()}:queue"


def _active_key():
    return f"{_prefix()}:active"


def _job_key(job_id):
    return f"{_prefix()}:job:{job_id}"


def _result_key(job_id):
    return f"{_prefix()}:result:{job_id}"


def _queue_position(client, job_id):
    """
    Index of job_id within the queue list, or None if it isn't there anymore
    (already dispatched). Older Redis builds (< 6.0.6, notably the Windows
    port this project's dev environment ships with) don't support LPOS, so
    this scans the list in Python instead - queues here are expected to stay
    small (bounded by realistic report traffic).
    """
    try:
        return client.lrange(_queue_key(), 0, -1).index(job_id)
    except ValueError:
        return None


def enqueue(request, view_key, query_params, title):
    """
    Records a new report job and returns its job id. Attempts to dispatch it
    (and any other queued jobs that now fit) immediately.
    """
    client = _get_redis()
    clean_params = {
        k: v for k, v in (query_params or {}).items() if v not in (None, "")
    }
    if request.session.session_key is None:
        request.session.save()
    job_id = uuid.uuid4().hex
    job_hash = {
        "view_key": view_key,
        "title": title or "",
        "session_key": request.session.session_key,
        "created_at": time.time(),
        "status": "queued",
        "query_params": json.dumps(clean_params),
    }
    key = _job_key(job_id)
    client.hmset(key, job_hash)
    client.expire(key, settings.REPORT_QUEUE_JOB_TIMEOUT + settings.REPORT_QUEUE_RESULT_TTL)
    client.rpush(_queue_key(), job_id)
    _try_dispatch_next()
    return job_id


def get_status(job_id, requesting_session_key=None):
    """
    Returns a JSON-serializable status dict for a job, or None if the job
    doesn't exist (or doesn't belong to requesting_session_key, when given).
    """
    client = _get_redis()
    job = client.hgetall(_job_key(job_id))
    if not job:
        return None
    if requesting_session_key is not None and job.get("session_key") != requesting_session_key:
        return None

    status = job.get("status", "queued")
    now = time.time()
    started_at = float(job.get("started_at") or job.get("created_at") or now)
    position = 0
    if status == "queued":
        found_at = _queue_position(client, job_id)
        position = found_at if found_at is not None else 0
    if status == "running" and (now - started_at) > settings.REPORT_QUEUE_JOB_TIMEOUT:
        status = "timeout"

    return {
        "job_id": job_id,
        "status": status,
        "title": job.get("title"),
        "position": position,
        "active": client.zcard(_active_key()),
        "max_concurrent": settings.MAX_CONCURRENT_REPORTS,
        "error": job.get("error"),
    }


def get_result(job_id, requesting_session_key=None):
    """Returns the rendered report HTML for a ready job, or None."""
    client = _get_redis()
    if requesting_session_key is not None:
        job = client.hgetall(_job_key(job_id))
        if not job or job.get("session_key") != requesting_session_key:
            return None
    return client.get(_result_key(job_id))


def refresh_csrf_token(request, html):
    """
    Report pages embed a csrf token for the "save closed report" AJAX call
    (see report_base.html's saveHtml()). That token was generated against a
    synthetic request when the report was rendered in the background, so it
    won't validate for whoever actually views the cached page. Swap in a
    token that's valid for the real, current request.
    """
    token = get_token(request)
    return _CSRF_JS_PATTERN.sub(lambda m: m.group(1) + token + m.group(3), html, count=1)


def _get_job(job_id):
    client = _get_redis()
    data = client.hgetall(_job_key(job_id))
    if not data:
        return None
    data["query_params"] = json.loads(data.get("query_params") or "{}")
    return data


def _set_status(job_id, status, error=None):
    client = _get_redis()
    mapping = {"status": status}
    if status == "running":
        mapping["started_at"] = time.time()
    if error:
        mapping["error"] = error
    client.hmset(_job_key(job_id), mapping)
    if status in ("ready", "error"):
        client.expire(_job_key(job_id), settings.REPORT_QUEUE_RESULT_TTL)


def _build_fake_request(job):
    """
    Builds a throwaway request carrying the submitter's session so the
    registered report view can run exactly as it would for a real request.
    """
    fake_request = _request_factory.get(f"/{job['view_key']}", data=job["query_params"])
    fake_request.session = SessionStore(session_key=job["session_key"])
    fake_request._messages = FallbackStorage(fake_request)
    return fake_request


def _run_job(job_id):
    client = _get_redis()
    job = None
    try:
        job = _get_job(job_id)
        if job is None:
            return
        view_func = REPORT_VIEW_REGISTRY.get(job["view_key"])
        if view_func is None:
            raise LookupError(f"No report is registered for '{job['view_key']}'")
        fake_request = _build_fake_request(job)
        if not fake_request.session.get("session_id"):
            raise PermissionError(
                "Your session expired while this report was queued. "
                "Please log in again and resubmit it."
            )
        response = view_func(fake_request)
        if response.status_code != 200:
            raise RuntimeError("Report generation failed. Please try again.")
        content = response.content.decode(response.charset or "utf-8")
        client.set(_result_key(job_id), content, ex=settings.REPORT_QUEUE_RESULT_TTL)
        _set_status(job_id, "ready")
    except Exception as e:
        view_key = job["view_key"] if job else "unknown"
        logger.error(f"Report job {job_id} ({view_key}) failed: {e}", exc_info=True)
        _set_status(job_id, "error", error=str(e))
    finally:
        client.zrem(_active_key(), job_id)
        _try_dispatch_next()


def _try_dispatch_next():
    script = _get_dispatch_script()
    while True:
        job_id = script(
            keys=[_active_key(), _queue_key()],
            args=[settings.MAX_CONCURRENT_REPORTS, time.time(), settings.REPORT_QUEUE_JOB_TIMEOUT],
        )
        if not job_id:
            break
        _set_status(job_id, "running")
        threading.Thread(
            target=_run_job, args=(job_id,), daemon=True, name=f"report-job-{job_id[:8]}"
        ).start()


def start_background_poller(interval=2.0):
    """
    Safety net so queued jobs still get dispatched even if no enqueue/completion
    event happens to trigger it (e.g. after a worker crashes mid-job). Idempotent
    - safe to call from every worker process's AppConfig.ready().
    """
    global _poller_started
    with _poller_lock:
        if _poller_started:
            return
        _poller_started = True

    def _loop():
        while True:
            try:
                _try_dispatch_next()
            except Exception as e:
                logger.debug(f"Report queue poll skipped: {e}")
            time.sleep(interval)

    threading.Thread(target=_loop, daemon=True, name="report-queue-poller").start()
