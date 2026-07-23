import json
import os
import time
from typing import Any, Optional


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _truthy_env(name: str, default: str = "") -> bool:
    v = (os.environ.get(name) or default).strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _max_chars() -> int:
    try:
        return int((os.environ.get("VISTORA_LLM_AUDIT_LOG_MAX_CHARS") or "5000").strip())
    except Exception:
        return 5000


def _mode() -> str:
    return (os.environ.get("VISTORA_LLM_AUDIT_LOG_MODE") or "metadata_only").strip().lower()


def _safe_truncate(s: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(s) <= max_len:
        return s
    return s[:max_len] + "...<truncated>"


def _get_req_id() -> Optional[str]:
    # Reuse same env-based correlation. Streamlit root span patch sets a ContextVar req_id,
    # but we keep this best-effort and cheap.
    try:
        return (os.environ.get("REQ_ID") or os.environ.get("X_REQUEST_ID") or "").strip() or None
    except Exception:
        return None


def _get_trace_id() -> Optional[str]:
    try:
        from opentelemetry import trace  # type: ignore

        span = trace.get_current_span()
        if span is None:
            return None
        ctx = span.get_span_context()
        if ctx is None:
            return None
        if not getattr(ctx, "is_valid", True):
            # older otel might not have is_valid
            pass
        trace_id = getattr(ctx, "trace_id", None)
        if trace_id is None:
            return None
        return format(trace_id, "032x")
    except Exception:
        return None


def _is_databricks_invocation(url: str) -> bool:
    try:
        u = (url or "")
        return ("/serving-endpoints/" in u) and ("/invocations" in u)
    except Exception:
        return False


def _extract_endpoint_name(url: str) -> Optional[str]:
    try:
        # .../serving-endpoints/<endpoint>/invocations
        parts = url.split("/serving-endpoints/", 1)
        if len(parts) != 2:
            return None
        rest = parts[1]
        endpoint = rest.split("/", 1)[0]
        return endpoint or None
    except Exception:
        return None


def _emit(event: dict[str, Any]) -> None:
    try:
        print(json.dumps(event, ensure_ascii=False))
    except Exception:
        pass


def patch_all() -> None:
    if not _truthy_env("VISTORA_LLM_AUDIT_LOG", default="0"):
        return

    try:
        import requests  # type: ignore
    except Exception:
        return

    # Patch only once
    if getattr(requests, "__vistora_llm_audit_patched__", False):
        return

    orig_request = getattr(requests.sessions.Session, "request", None)
    if not callable(orig_request):
        return

    def request(self, method, url, **kwargs):  # type: ignore[no-untyped-def]
        if not _is_databricks_invocation(str(url)):
            return orig_request(self, method, url, **kwargs)

        start = time.time()
        trace_id = _get_trace_id()
        req_id = _get_req_id()
        endpoint_name = _extract_endpoint_name(str(url))

        m = _mode()
        max_len = _max_chars()

        req_payload: Any = None
        if m != "metadata_only":
            # prefer json= payload; fallback to data=
            if "json" in kwargs:
                req_payload = kwargs.get("json")
            else:
                req_payload = kwargs.get("data")

        _emit(
            {
                "ts": _now_iso(),
                "event": "llm.request",
                "llm.provider": "databricks_model_serving",
                "endpoint": endpoint_name or "",
                "method": str(method),
                "url": str(url),
                "trace_id": trace_id or "",
                "req_id": req_id or "",
                "request": req_payload if m != "metadata_only" else None,
            }
        )

        try:
            resp = orig_request(self, method, url, **kwargs)
        except Exception as exc:
            latency_ms = int((time.time() - start) * 1000)
            _emit(
                {
                    "ts": _now_iso(),
                    "event": "llm.response",
                    "llm.provider": "databricks_model_serving",
                    "endpoint": endpoint_name or "",
                    "trace_id": trace_id or "",
                    "req_id": req_id or "",
                    "status": "error",
                    "latency_ms": latency_ms,
                    "error": str(exc),
                }
            )
            raise

        latency_ms = int((time.time() - start) * 1000)

        resp_text: Optional[str] = None
        if m != "metadata_only":
            try:
                resp_text = _safe_truncate(getattr(resp, "text", "") or "", max_len)
            except Exception:
                resp_text = None

        _emit(
            {
                "ts": _now_iso(),
                "event": "llm.response",
                "llm.provider": "databricks_model_serving",
                "endpoint": endpoint_name or "",
                "trace_id": trace_id or "",
                "req_id": req_id or "",
                "status": "success" if getattr(resp, "ok", False) else "error",
                "status_code": getattr(resp, "status_code", None),
                "latency_ms": latency_ms,
                "response_text": resp_text if m != "metadata_only" else None,
            }
        )

        return resp

    try:
        setattr(requests.sessions.Session, "request", request)
        setattr(requests, "__vistora_llm_audit_patched__", True)
    except Exception:
        pass
