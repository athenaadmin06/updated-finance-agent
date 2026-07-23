import os
import re
import json
import time
import uuid
import contextvars
from typing import Any, Optional


_REQ_ID_CVAR: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "vistora_req_id", default=None
)

_AGENT_ID_CVAR: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "vistora_agent_id", default=None
)


def _new_req_id() -> str:
    return uuid.uuid4().hex


def _normalize_header_val(v: Any) -> str | None:
    try:
        if v is None:
            return None
        s = str(v).strip()
        return s or None
    except Exception:
        return None


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y")


def _effective_trace_endpoint() -> str | None:
    # Prefer signal-specific endpoint if provided; fall back to the generic OTLP endpoint.
    ep = (os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or "").strip()
    if ep:
        return ep
    ep = (os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip()
    return ep or None


def _has_s3_span_exporter(provider: Any) -> bool:
    try:
        spm = getattr(provider, "_active_span_processor", None)
        processors = getattr(spm, "_span_processors", None)
        if processors is None:
            return False
        for p in list(processors):
            exp = getattr(p, "_exporter", None)
            if exp is None:
                continue
            if exp.__class__.__name__ == "_S3JsonlSpanExporter":
                return True
    except Exception:
        return False
    return False


def _scrub_sensitive(value: Any) -> Any:
    # Production default: do not emit SQL params / token-like values.
    if _bool_env("VISTORA_ALLOW_SENSITIVE_LOGS", default=False):
        return value
    try:
        if value is None:
            return None
        if isinstance(value, (str, bytes)):
            return "[REDACTED]"
        if isinstance(value, dict):
            return {str(k): "[REDACTED]" for k in value.keys()}
        if isinstance(value, (list, tuple)):
            return ["[REDACTED]" for _ in value]
    except Exception:
        return "[REDACTED]"
    return "[REDACTED]"


def _get_req_id() -> Optional[str]:
    try:
        rid = _REQ_ID_CVAR.get()
        if rid:
            return rid
    except Exception:
        pass
    return (os.environ.get("REQ_ID") or os.environ.get("X_REQUEST_ID") or "").strip() or None


def _get_agent_id() -> Optional[str]:
    try:
        aid = _AGENT_ID_CVAR.get()
        if aid:
            return aid
    except Exception:
        pass
    return None


def _req_id_from_wsgi_environ(environ: Any) -> str | None:
    try:
        if not environ:
            return None
        return _normalize_header_val(environ.get("HTTP_X_REQUEST_ID") or environ.get("HTTP_X_REQUESTID"))
    except Exception:
        return None


def _req_id_from_asgi_scope(scope: Any) -> str | None:
    try:
        if not scope:
            return None
        headers = scope.get("headers") or []
        for k, v in headers:
            try:
                if bytes(k).lower() in (b"x-request-id", b"x-requestid"):
                    return _normalize_header_val(bytes(v).decode("utf-8", errors="ignore"))
            except Exception:
                continue
    except Exception:
        return None
    return None


def _get_tracer():
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # type: ignore
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import SpanExporter  # type: ignore
        from opentelemetry.sdk.trace.export import SpanExportResult  # type: ignore
    except Exception:
        return None

    class _S3JsonlSpanExporter(SpanExporter):
        def __init__(self) -> None:
            super().__init__()
            self._buf: list[str] = []
            self._last_flush = time.time()
            try:
                self._interval_s = int(os.environ.get("VISTORA_S3_SPAN_EXPORT_INTERVAL_SECONDS", "60").strip() or "60")
            except Exception:
                self._interval_s = 60
            try:
                self._max_buf = int(os.environ.get("VISTORA_S3_SPAN_EXPORT_MAX_BUFFER", "256").strip() or "256")
            except Exception:
                self._max_buf = 256

        def export(self, spans) -> "SpanExportResult":  # type: ignore[override]
            try:
                for s in spans or []:
                    try:
                        self._buf.append(self._span_to_json(s))
                    except Exception:
                        continue

                now = time.time()
                if len(self._buf) >= self._max_buf or (now - self._last_flush) >= self._interval_s:
                    self._flush_to_s3()
                    self._last_flush = now
                return SpanExportResult.SUCCESS
            except Exception:
                return SpanExportResult.FAILURE

        def shutdown(self) -> None:  # type: ignore[override]
            try:
                self._flush_to_s3()
            except Exception:
                pass

        def _span_to_json(self, span) -> str:
            ctx = span.get_span_context() if span is not None else None
            trace_id = format(getattr(ctx, "trace_id", 0) or 0, "032x")
            span_id = format(getattr(ctx, "span_id", 0) or 0, "016x")

            events = []
            for ev in getattr(span, "events", []) or []:
                try:
                    events.append(
                        {
                            "name": getattr(ev, "name", ""),
                            "timestamp": getattr(ev, "timestamp", None),
                            "attributes": dict(getattr(ev, "attributes", {}) or {}),
                        }
                    )
                except Exception:
                    continue

            payload = {
                "name": getattr(span, "name", ""),
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": format(getattr(span, "parent", None).span_id, "016x") if getattr(span, "parent", None) else None,
                "start_time_unix_nano": getattr(span, "start_time", None),
                "end_time_unix_nano": getattr(span, "end_time", None),
                "attributes": dict(getattr(span, "attributes", {}) or {}),
                "events": events,
            }
            return json.dumps(payload, ensure_ascii=False)

        def _flush_to_s3(self) -> None:
            if not self._buf:
                return

            if not _bool_env("VISTORA_S3_SPAN_EXPORT", default=False):
                self._buf.clear()
                return

            bucket = (
                os.environ.get("S3_LOGS_BUCKET")
                or os.environ.get("S3_ARTIFACTS_BUCKET")
                or ""
            ).strip()
            if not bucket:
                return

            try:
                import boto3  # type: ignore
            except Exception:
                return

            region = (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "").strip() or None
            s3 = boto3.client("s3", region_name=region)

            prefix = (
                os.environ.get("S3_LOGS_PREFIX")
                or os.environ.get("S3_ARTIFACTS_PREFIX")
                or "logs"
            ).strip().strip("/")
            date_path = time.strftime("%Y/%m/%d", time.gmtime())
            ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            key = f"{prefix}/{date_path}/spans_{ts}_{uuid.uuid4().hex}.jsonl"

            body = "\n".join(self._buf) + "\n"
            self._buf.clear()

            try:
                s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=body.encode("utf-8"),
                    ContentType="application/x-ndjson",
                )
            except Exception:
                # On failure, we drop the batch to avoid unbounded memory growth.
                return

    # If an SDK provider already exists, reuse it (don't override), but still return a tracer.
    try:
        existing = trace.get_tracer_provider()
        if isinstance(existing, TracerProvider):
            # Add S3 exporter to existing provider if enabled and not already added
            if _bool_env("VISTORA_S3_SPAN_EXPORT", default=False):
                # Check if we already added our exporter (via a marker or by scanning processors)
                already = getattr(existing, "__vistora_s3_exporter_added__", False) or _has_s3_span_exporter(existing)
                if not already:
                    existing.add_span_processor(BatchSpanProcessor(_S3JsonlSpanExporter()))
                    try:
                        setattr(existing, "__vistora_s3_exporter_added__", True)
                    except Exception:
                        pass
            return trace.get_tracer("vistora.otel_s3")
    except Exception:
        pass

    resource = Resource.create({"service.name": os.environ.get("OTEL_SERVICE_NAME", "vistora")})
    provider = TracerProvider(resource=resource)

    if not _bool_env("VISTORA_DISABLE_OTLP", default=False):
        endpoint = _effective_trace_endpoint()
        if endpoint:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        else:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

    if _bool_env("VISTORA_OTEL_CONSOLE_EXPORTER", default=False):
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    if _bool_env("VISTORA_S3_SPAN_EXPORT", default=False):
        provider.add_span_processor(BatchSpanProcessor(_S3JsonlSpanExporter()))
        try:
            setattr(provider, "__vistora_s3_exporter_added__", True)
        except Exception:
            pass

    trace.set_tracer_provider(provider)
    return trace.get_tracer("vistora.otel_s3")


def _span_trace_id_hex(span) -> Optional[str]:
    try:
        ctx = span.get_span_context()
        if ctx is None:
            return None
        return format(ctx.trace_id, "032x")
    except Exception:
        return None


def _s3_put_text(key: str, body: str, content_type: str) -> Optional[str]:
    if not _bool_env("VISTORA_ENABLE_ARTIFACT_UPLOAD", default=False):
        return None
    bucket = (os.environ.get("S3_ARTIFACTS_BUCKET") or "").strip()
    if not bucket:
        return None

    try:
        import boto3  # type: ignore

        region = (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "").strip() or None
        s3 = boto3.client("s3", region_name=region)
        s3.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"), ContentType=content_type)
        return f"s3://{bucket}/{key}"
    except Exception:
        return None


def _artifact_key(trace_id: str, data_platform: str, ext: str) -> str:
    prefix = (os.environ.get("S3_ARTIFACTS_PREFIX") or "artifacts").strip().strip("/")
    date_path = time.strftime("%Y/%m/%d", time.gmtime())
    return f"{prefix}/{date_path}/{trace_id}_{data_platform}.{ext}"


def _emit_artifact_written(span, *, data_platform: str, artifact_uri: str, artifact_type: str) -> None:
    try:
        span.add_event(
            "rag.artifact_written",
            {
                "data_platform": data_platform,
                "artifact_uri": artifact_uri,
                "artifact_type": artifact_type,
                "report_generated_at": _now_iso(),
            },
        )
    except Exception:
        pass


def _maybe_emit_dummy_artifact(span) -> None:
    try:
        if not _bool_env("VISTORA_DUMMY_ARTIFACT", default=False):
            return

        trace_id = _span_trace_id_hex(span)
        if not trace_id:
            return

        payload = {
            "type": "vistora_dummy_artifact",
            "ts": _now_iso(),
            "trace_id": trace_id,
        }
        body = json.dumps(payload, ensure_ascii=False)
        key = _artifact_key(trace_id, "dummy", "json")
        uri = _s3_put_text(key, body, "application/json")
        if not uri:
            return

        _emit_artifact_written(span, data_platform="dummy", artifact_uri=uri, artifact_type="json")
        _emit_artifact_written_log(
            data_platform="dummy",
            artifact_uri=uri,
            artifact_type="json",
            trace_id=trace_id,
        )
    except Exception:
        pass


def _emit_artifact_written_log(*, data_platform: str, artifact_uri: str, artifact_type: str, trace_id: str) -> None:
    try:
        if not _bool_env("VISTORA_ENABLE_ARTIFACT_LOGS", default=False):
            return
        print(
            json.dumps(
                {
                    "ts": _now_iso(),
                    "event": "rag.artifact_written",
                    "data_platform": data_platform,
                    "artifact_uri": artifact_uri,
                    "artifact_type": artifact_type,
                    "trace_id": trace_id,
                    "req_id": _get_req_id() or "",
                },
                ensure_ascii=False,
            )
        )
    except Exception:
        pass


def _extract_customer_id_from_filter(filter_obj: Any) -> str | None:
    try:
        if isinstance(filter_obj, dict) and "customer_id" in filter_obj:
            v = filter_obj.get("customer_id")
            if isinstance(v, dict):
                for op in ("$eq", "eq"):
                    if op in v:
                        return str(v[op])
            return str(v)
    except Exception:
        return None
    return None


def _serialize_pinecone_result(res: Any) -> str:
    payload: dict[str, Any] = {
        "type": "pinecone_query_result",
    }
    try:
        matches = getattr(res, "matches", None)
        if matches is not None:
            out_matches = []
            for m in matches:
                try:
                    out_matches.append(
                        {
                            "id": getattr(m, "id", None),
                            "score": getattr(m, "score", None),
                            "metadata": getattr(m, "metadata", None),
                            "values": getattr(m, "values", None),
                        }
                    )
                except Exception:
                    continue
            payload["matches"] = out_matches
    except Exception:
        pass

    return json.dumps(payload, ensure_ascii=False)


def _patch_streamlit_root_span() -> None:
    try:
        from streamlit.runtime.scriptrunner.script_runner import ScriptRunner  # type: ignore
    except Exception:
        return

    if getattr(ScriptRunner, "__vistora_otel_s3_patched__", False):
        return

    tracer = _get_tracer()
    orig_run_script = getattr(ScriptRunner, "_run_script", None)
    if not callable(orig_run_script):
        return

    # Counter to skip first run (Streamlit runs script on startup)
    _run_count = [0]

    def _run_script(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        _run_count[0] += 1
        print(f"[vistora] _run_script invoked, count={_run_count[0]}")
        
        # Skip rag.request span on first run (startup)
        if _run_count[0] == 1 and _bool_env("VISTORA_SKIP_FIRST_RUN", default=True):
            print(f"[vistora] skipping first run (startup)")
            return orig_run_script(self, *args, **kwargs)
        
        # Use existing req_id/agent_id from session_state if set (persists across reruns until Submit)
        try:
            import streamlit as st  # type: ignore
            existing_req_id = st.session_state.get("vistora_req_id")
            existing_agent_id = st.session_state.get("vistora_agent_id")
            print(f"[vistora] session_state req_id={existing_req_id}, agent_id={existing_agent_id}")
        except Exception:
            existing_req_id = None
            existing_agent_id = None
        
        if existing_req_id:
            new_req_id = existing_req_id
        else:
            new_req_id = _new_req_id()

        if existing_agent_id:
            new_agent_id = existing_agent_id
        else:
            new_agent_id = _new_req_id()

        token = _REQ_ID_CVAR.set(new_req_id)
        token_agent = _AGENT_ID_CVAR.set(new_agent_id)
        print(f"[vistora] set ContextVar req_id={new_req_id}, agent_id={new_agent_id}")

        if tracer is None:
            try:
                return orig_run_script(self, *args, **kwargs)
            finally:
                try:
                    _REQ_ID_CVAR.reset(token)
                except Exception:
                    pass
                try:
                    _AGENT_ID_CVAR.reset(token_agent)
                except Exception:
                    pass

        with tracer.start_as_current_span("rag.request") as span:
            span.set_attribute("vistora.req_id", new_req_id)
            if new_agent_id:
                span.set_attribute("vistora.agent_id", new_agent_id)
            span.set_attribute("app.framework", "streamlit")
            print(f"[vistora] created rag.request span, agent_id={new_agent_id}")
            try:
                _maybe_emit_dummy_artifact(span)
                return orig_run_script(self, *args, **kwargs)
            finally:
                try:
                    _REQ_ID_CVAR.reset(token)
                except Exception:
                    pass
                try:
                    _AGENT_ID_CVAR.reset(token_agent)
                except Exception:
                    pass

    try:
        setattr(ScriptRunner, "_run_script", _run_script)
        setattr(ScriptRunner, "__vistora_otel_s3_patched__", True)
    except Exception:
        pass


def _patch_pinecone_otel_s3() -> None:
    try:
        import pinecone  # type: ignore
    except Exception:
        return

    tracer = _get_tracer()

    # Check if already patched at module level
    if getattr(pinecone, "__vistora_otel_s3_patched__", False):
        return

    # Handle new Pinecone client (pinecone.Pinecone)
    PineconeCls = getattr(pinecone, "Pinecone", None)
    if PineconeCls is not None and not getattr(PineconeCls, "__vistora_otel_s3_patched__", False):
        orig_pinecone_init = getattr(PineconeCls, "__init__", None)
        if callable(orig_pinecone_init):
            def _patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                orig_pinecone_init(self, *args, **kwargs)
                # Patch the Index method on this instance
                orig_index_method = getattr(self, "Index", None)
                if callable(orig_index_method) and not getattr(self, "__vistora_index_patched__", False):
                    def _patched_index(*i_args, **i_kwargs):  # type: ignore[no-untyped-def]
                        idx = orig_index_method(*i_args, **i_kwargs)
                        if idx is not None:
                            _patch_pinecone_index_object(idx, tracer)
                        return idx
                    setattr(self, "Index", _patched_index)
                    setattr(self, "__vistora_index_patched__", True)
            try:
                setattr(PineconeCls, "__init__", _patched_init)
                setattr(PineconeCls, "__vistora_otel_s3_patched__", True)
            except Exception:
                pass

    # Handle old pinecone.Index class (legacy client)
    IndexCls = getattr(pinecone, "Index", None)
    if IndexCls is not None and not getattr(IndexCls, "__vistora_otel_s3_patched__", False):
        _patch_pinecone_index_class(IndexCls, tracer)
        try:
            setattr(IndexCls, "__vistora_otel_s3_patched__", True)
        except Exception:
            pass

    try:
        setattr(pinecone, "__vistora_otel_s3_patched__", True)
    except Exception:
        pass


def _patch_pinecone_index_object(idx_obj: Any, tracer) -> None:
    """Patch a specific Pinecone index instance."""
    if getattr(idx_obj, "__vistora_otel_s3_patched__", False):
        return

    orig_query = getattr(idx_obj, "query", None)
    if not callable(orig_query):
        return

    def query(*args, **kwargs):  # type: ignore[no-untyped-def]
        req_id = _get_req_id()
        agent_id = _get_agent_id()
        top_k = kwargs.get("top_k")
        customer_id = _extract_customer_id_from_filter(kwargs.get("filter"))

        if tracer is None:
            return orig_query(*args, **kwargs)

        with tracer.start_as_current_span("rag.source_access") as span:
            span.set_attribute("rag.source.name", "pinecone")
            if req_id:
                span.set_attribute("vistora.req_id", req_id)
            if agent_id:
                span.set_attribute("vistora.agent_id", agent_id)
            if top_k is not None:
                try:
                    span.set_attribute("rag.top_k", int(top_k))
                except Exception:
                    pass
            if customer_id:
                span.set_attribute("rag.customer_id", customer_id)

            res = orig_query(*args, **kwargs)

            trace_id = _span_trace_id_hex(span)
            if trace_id:
                body = _serialize_pinecone_result(res)
                key = _artifact_key(trace_id, "pinecone", "json")
                uri = _s3_put_text(key, body, "application/json")
                if uri:
                    _emit_artifact_written(
                        span,
                        data_platform="pinecone",
                        artifact_uri=uri,
                        artifact_type="json",
                    )
                    _emit_artifact_written_log(
                        data_platform="pinecone",
                        artifact_uri=uri,
                        artifact_type="json",
                        trace_id=trace_id,
                    )

            return res

    try:
        setattr(idx_obj, "query", query)
        setattr(idx_obj, "__vistora_otel_s3_patched__", True)
    except Exception:
        pass


def _patch_pinecone_index_class(IndexCls: Any, tracer) -> None:
    """Patch the pinecone.Index class (legacy client)."""
    if getattr(IndexCls, "__vistora_otel_s3_patched__", False):
        return

    orig_query = getattr(IndexCls, "query", None)
    if not callable(orig_query):
        return

    def query(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        req_id = _get_req_id()
        agent_id = _get_agent_id()
        top_k = kwargs.get("top_k")
        customer_id = _extract_customer_id_from_filter(kwargs.get("filter"))

        if tracer is None:
            return orig_query(self, *args, **kwargs)

        with tracer.start_as_current_span("rag.source_access") as span:
            span.set_attribute("rag.source.name", "pinecone")
            if req_id:
                span.set_attribute("vistora.req_id", req_id)
            if agent_id:
                span.set_attribute("vistora.agent_id", agent_id)
            if top_k is not None:
                try:
                    span.set_attribute("rag.top_k", int(top_k))
                except Exception:
                    pass
            if customer_id:
                span.set_attribute("rag.customer_id", customer_id)

            res = orig_query(self, *args, **kwargs)

            trace_id = _span_trace_id_hex(span)
            if trace_id:
                body = _serialize_pinecone_result(res)
                key = _artifact_key(trace_id, "pinecone", "json")
                uri = _s3_put_text(key, body, "application/json")
                if uri:
                    _emit_artifact_written(
                        span,
                        data_platform="pinecone",
                        artifact_uri=uri,
                        artifact_type="json",
                    )
                    _emit_artifact_written_log(
                        data_platform="pinecone",
                        artifact_uri=uri,
                        artifact_type="json",
                        trace_id=trace_id,
                    )

            return res

    try:
        setattr(IndexCls, "query", query)
        setattr(IndexCls, "__vistora_otel_s3_patched__", True)
    except Exception:
        pass


def _patch_databricks_sql_otel_s3() -> None:
    try:
        from databricks import sql  # type: ignore
    except Exception:
        return

    if getattr(sql, "__vistora_otel_s3_patched__", False):
        return

    orig_connect = getattr(sql, "connect", None)
    if not callable(orig_connect):
        return

    tracer = _get_tracer()

    def connect(*args, **kwargs):  # type: ignore[no-untyped-def]
        conn = orig_connect(*args, **kwargs)
        orig_cursor = getattr(conn, "cursor", None)
        if not callable(orig_cursor):
            return conn

        class _CursorProxy:
            def __init__(self, inner):  # type: ignore[no-untyped-def]
                self._inner = inner
                self._vistora_trace_id = None  # stored during execute() for use in fetchall()/fetchmany()

            def __enter__(self):  # type: ignore[no-untyped-def]
                enter = getattr(self._inner, "__enter__", None)
                if callable(enter):
                    enter()
                return self

            def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
                exit_ = getattr(self._inner, "__exit__", None)
                if callable(exit_):
                    return exit_(exc_type, exc, tb)
                close = getattr(self._inner, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass
                return False

            def execute(self, query, params=None):  # type: ignore[no-untyped-def]
                req_id = _get_req_id()
                agent_id = _get_agent_id()

                if tracer is None:
                    return (
                        self._inner.execute(query, params)
                        if params is not None
                        else self._inner.execute(query)
                    )

                with tracer.start_as_current_span("rag.source_access") as span:
                    span.set_attribute("rag.source.name", "databricks")
                    span.set_attribute("db.system", "databricks")
                    if req_id:
                        span.set_attribute("vistora.req_id", req_id)
                    if agent_id:
                        span.set_attribute("vistora.agent_id", agent_id)

                    out = (
                        self._inner.execute(query, params)
                        if params is not None
                        else self._inner.execute(query)
                    )

                    trace_id = _span_trace_id_hex(span)
                    self._vistora_trace_id = trace_id  # store for fetchall()/fetchmany()
                    self._vistora_query = str(query)
                    self._vistora_params = _scrub_sensitive(params)
                    
                    # Upload artifact with query info (will be updated by fetch with rows)
                    if trace_id and _bool_env("VISTORA_ENABLE_ARTIFACT_UPLOAD", default=False):
                        payload = {
                            "type": "databricks_result",
                            "query": str(query),
                            "params": _scrub_sensitive(params),
                            "row_count": 0,
                            "rows": [],
                        }
                        body = json.dumps(payload, ensure_ascii=False, default=str)
                        key = _artifact_key(trace_id, "databricks_result", "json")
                        uri = _s3_put_text(key, body, "application/json")
                        if uri:
                            _emit_artifact_written(
                                span,
                                data_platform="databricks",
                                artifact_uri=uri,
                                artifact_type="json",
                            )
                            _emit_artifact_written_log(
                                data_platform="databricks",
                                artifact_uri=uri,
                                artifact_type="json",
                                trace_id=trace_id,
                            )

                    return out

            def fetchall(self):  # type: ignore[no-untyped-def]
                rows = self._inner.fetchall()
                try:
                    if _bool_env("VISTORA_ENABLE_ARTIFACT_UPLOAD", default=False):
                        trace_id = getattr(self, "_vistora_trace_id", None)
                        if trace_id and rows:
                            max_rows = int(os.environ.get("VISTORA_DUMP_DBX_MAX_ROWS", "200").strip() or "200")
                            payload = {
                                "type": "databricks_result",
                                "query": getattr(self, "_vistora_query", ""),
                                "params": getattr(self, "_vistora_params", {}),
                                "row_count": len(rows),
                                "rows": _scrub_sensitive(rows[:max_rows]) if rows else [],
                            }
                            body = json.dumps(payload, ensure_ascii=False, default=str)
                            key = _artifact_key(trace_id, "databricks_result", "json")
                            _s3_put_text(key, body, "application/json")
                except Exception:
                    pass
                return rows

            def fetchone(self):  # type: ignore[no-untyped-def]
                row = self._inner.fetchone()
                try:
                    if _bool_env("VISTORA_ENABLE_ARTIFACT_UPLOAD", default=False):
                        trace_id = getattr(self, "_vistora_trace_id", None)
                        if trace_id and row:
                            # Handle row as tuple or dict
                            if isinstance(row, (list, tuple)):
                                rows_list = [row]
                            elif isinstance(row, dict):
                                rows_list = [row]
                            else:
                                rows_list = [row]
                            payload = {
                                "type": "databricks_result",
                                "query": getattr(self, "_vistora_query", ""),
                                "params": getattr(self, "_vistora_params", {}),
                                "row_count": 1,
                                "rows": _scrub_sensitive(rows_list),
                            }
                            body = json.dumps(payload, ensure_ascii=False, default=str)
                            key = _artifact_key(trace_id, "databricks_result", "json")
                            _s3_put_text(key, body, "application/json")
                except Exception:
                    pass
                return row

            def fetchmany(self, size=None):  # type: ignore[no-untyped-def]
                if size is not None:
                    rows = self._inner.fetchmany(size)
                else:
                    rows = self._inner.fetchmany()
                try:
                    if _bool_env("VISTORA_ENABLE_ARTIFACT_UPLOAD", default=False):
                        trace_id = getattr(self, "_vistora_trace_id", None)
                        if trace_id and rows:
                            max_rows = int(os.environ.get("VISTORA_DUMP_DBX_MAX_ROWS", "200").strip() or "200")
                            payload = {
                                "type": "databricks_result",
                                "query": getattr(self, "_vistora_query", ""),
                                "params": getattr(self, "_vistora_params", {}),
                                "row_count": len(rows),
                                "rows": _scrub_sensitive(rows[:max_rows]) if rows else [],
                            }
                            body = json.dumps(payload, ensure_ascii=False, default=str)
                            key = _artifact_key(trace_id, "databricks_result", "json")
                            _s3_put_text(key, body, "application/json")
                except Exception:
                    pass
                return rows

            def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
                return getattr(self._inner, name)

        def cursor(*c_args, **c_kwargs):  # type: ignore[no-untyped-def]
            cur = orig_cursor(*c_args, **c_kwargs)
            return _CursorProxy(cur)

        setattr(conn, "cursor", cursor)
        return conn

    try:
        setattr(sql, "connect", connect)
        setattr(sql, "__vistora_otel_s3_patched__", True)
    except Exception:
        pass


def patch_all() -> None:
    _patch_streamlit_root_span()
    _patch_pinecone_otel_s3()
    _patch_databricks_sql_otel_s3()

    try:
        from .llm_audit_databricks_requests import patch_all as _llm_audit_patch_all

        _llm_audit_patch_all()
    except Exception:
        pass
