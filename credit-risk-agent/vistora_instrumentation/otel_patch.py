import os
import re
import uuid
import contextvars
from typing import Any


_REQ_ID_CVAR: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "vistora_req_id", default=None
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


def _get_req_id() -> str | None:
    cvar_req_id = _REQ_ID_CVAR.get()
    if cvar_req_id:
        return cvar_req_id
    return (os.environ.get("REQ_ID") or os.environ.get("X_REQUEST_ID") or "").strip() or None


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


def _get_tracer():
    try:
        from opentelemetry import trace  # type: ignore

        return trace.get_tracer("vistora.instrumentation")
    except Exception:
        return None


def _patch_pinecone_spans() -> None:
    try:
        import pinecone  # type: ignore
    except Exception:
        return

    tracer = _get_tracer()

    def _wrap_index_query(index_obj):  # type: ignore[no-untyped-def]
        orig_query = getattr(index_obj, "query", None)
        if not callable(orig_query):
            return
        if getattr(index_obj, "__vistora_otel_query_patched__", False):
            return

        def query(*args, **kwargs):  # type: ignore[no-untyped-def]
            req_id = _get_req_id()
            top_k = kwargs.get("top_k")
            customer_id = _extract_customer_id_from_filter(kwargs.get("filter"))

            if tracer is None:
                return orig_query(*args, **kwargs)

            with tracer.start_as_current_span("rag.source_access") as span:
                span.set_attribute("rag.source.name", "pinecone")
                if req_id:
                    span.set_attribute("vistora.req_id", req_id)
                if top_k is not None:
                    try:
                        span.set_attribute("rag.top_k", int(top_k))
                    except Exception:
                        pass
                if customer_id:
                    span.set_attribute("rag.customer_id", customer_id)

                res = orig_query(*args, **kwargs)

                try:
                    matches = getattr(res, "matches", None)
                    if matches is not None:
                        span.set_attribute("rag.retrieved_chunks", int(len(matches)))
                except Exception:
                    pass

                return res

        try:
            setattr(index_obj, "query", query)
            setattr(index_obj, "__vistora_otel_query_patched__", True)
        except Exception:
            pass

    PineconeCls = getattr(pinecone, "Pinecone", None)
    if PineconeCls is not None and not getattr(PineconeCls, "__vistora_otel_patched__", False):
        orig_index_factory = getattr(PineconeCls, "Index", None)
        if callable(orig_index_factory):

            def Index(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                idx = orig_index_factory(self, *args, **kwargs)
                _wrap_index_query(idx)
                return idx

            try:
                setattr(PineconeCls, "Index", Index)
                setattr(PineconeCls, "__vistora_otel_patched__", True)
            except Exception:
                pass

    IndexCls = getattr(pinecone, "Index", None)
    if IndexCls is not None and not getattr(IndexCls, "__vistora_otel_patched__", False):
        orig_query = getattr(IndexCls, "query", None)
        if callable(orig_query):

            def query(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                req_id = _get_req_id()
                top_k = kwargs.get("top_k")
                customer_id = _extract_customer_id_from_filter(kwargs.get("filter"))

                if tracer is None:
                    return orig_query(self, *args, **kwargs)

                with tracer.start_as_current_span("rag.source_access") as span:
                    span.set_attribute("rag.source.name", "pinecone")
                    if req_id:
                        span.set_attribute("vistora.req_id", req_id)
                    if top_k is not None:
                        try:
                            span.set_attribute("rag.top_k", int(top_k))
                        except Exception:
                            pass
                    if customer_id:
                        span.set_attribute("rag.customer_id", customer_id)

                    res = orig_query(self, *args, **kwargs)

                    try:
                        matches = getattr(res, "matches", None)
                        if matches is not None:
                            span.set_attribute("rag.retrieved_chunks", int(len(matches)))
                    except Exception:
                        pass

                    return res

            try:
                setattr(IndexCls, "query", query)
                setattr(IndexCls, "__vistora_otel_patched__", True)
            except Exception:
                pass


def _patch_databricks_sql_spans() -> None:
    try:
        from databricks import sql  # type: ignore
    except Exception:
        return

    if getattr(sql, "__vistora_otel_patched__", False):
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
                table = None
                predicate = None

                try:
                    m = re.search(r"from\s+([^\s;]+)", str(query), flags=re.IGNORECASE)
                    if m:
                        table = m.group(1)
                except Exception:
                    table = None

                try:
                    if params and isinstance(params, dict):
                        cid = params.get("cid")
                        if cid is not None:
                            predicate = f"customer_id = '{cid}'"
                except Exception:
                    predicate = None

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
                    if table:
                        span.set_attribute("db.sql.table", table)
                    if predicate:
                        span.set_attribute("db.sql.predicate", predicate)

                    return (
                        self._inner.execute(query, params)
                        if params is not None
                        else self._inner.execute(query)
                    )

            def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
                return getattr(self._inner, name)

        def cursor(*c_args, **c_kwargs):  # type: ignore[no-untyped-def]
            cur = orig_cursor(*c_args, **c_kwargs)
            return _CursorProxy(cur)

        setattr(conn, "cursor", cursor)
        return conn

    setattr(sql, "connect", connect)
    setattr(sql, "__vistora_otel_patched__", True)


def _patch_streamlit_root_span() -> None:
    try:
        from streamlit.runtime.scriptrunner.script_runner import ScriptRunner  # type: ignore
    except Exception:
        return

    if getattr(ScriptRunner, "__vistora_otel_patched__", False):
        return

    tracer = _get_tracer()
    orig_run_script = getattr(ScriptRunner, "_run_script", None)
    if not callable(orig_run_script):
        return

    def _run_script(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        new_req_id = _new_req_id()
        token = _REQ_ID_CVAR.set(new_req_id)

        if tracer is None:
            try:
                return orig_run_script(self, *args, **kwargs)
            finally:
                try:
                    _REQ_ID_CVAR.reset(token)
                except Exception:
                    pass

        with tracer.start_as_current_span("rag.request") as span:
            span.set_attribute("vistora.req_id", new_req_id)
            span.set_attribute("app.framework", "streamlit")
            try:
                return orig_run_script(self, *args, **kwargs)
            finally:
                try:
                    _REQ_ID_CVAR.reset(token)
                except Exception:
                    pass

    setattr(ScriptRunner, "_run_script", _run_script)
    setattr(ScriptRunner, "__vistora_otel_patched__", True)


def patch_all() -> None:
    """Patch clients to emit OTel spans for forensic source-access tracing.

    Intended to be invoked in a startup wrapper that is run via opentelemetry-instrument.
    """

    _patch_streamlit_root_span()
    _patch_pinecone_spans()
    _patch_databricks_sql_spans()
