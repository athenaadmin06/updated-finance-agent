import os
import re
import time
import uuid
import contextvars
from typing import Any


_REQ_ID_CVAR: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "vistora_req_id", default=None
)

def _now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _get_req_id() -> str | None:
    cvar_req_id = _REQ_ID_CVAR.get()
    if cvar_req_id:
        return cvar_req_id
    return (os.environ.get("REQ_ID") or os.environ.get("X_REQUEST_ID") or "").strip() or None


def _append_line(path: str, line: str) -> None:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        if (os.environ.get("VISTORA_DEBUG_LOGGING") or "").strip() == "1":
            try:
                import sys

                sys.stderr.write(f"[vistora] Failed to append to {path}: {exc}\n")
            except Exception:
                pass


def _append_trace_jsonl(payload: dict[str, Any]) -> None:
    path = (os.environ.get("VISTORA_TRACE_LOG_PATH") or "").strip()
    if not path:
        return
    try:
        p = path
        if not os.path.isabs(p):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
            p = os.path.join(base_dir, p)
        _append_line(p, __import__("json").dumps(payload, ensure_ascii=False))
        log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
        _append_line(log_path, f"{_now_ts()} - agent - INFO - TRACE_JSONL_WRITTEN path={p}")
    except Exception:
        try:
            log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
            _append_line(log_path, f"{_now_ts()} - agent - INFO - TRACE_JSONL_FAILED path={path}")
        except Exception:
            pass
        return


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _write_local_artifact(*, req_id: str, payload: dict[str, Any]) -> str | None:
    try:
        base_dir = _repo_root()
        art_dir = os.path.join(base_dir, "local_artifacts")
        os.makedirs(art_dir, exist_ok=True)
        name = (req_id or "").strip() or uuid.uuid4().hex
        art_path = os.path.join(art_dir, f"{name}_databricks.json")
        with open(art_path, "w", encoding="utf-8") as f:
            __import__("json").dump(payload, f, ensure_ascii=False, indent=2)
        try:
            log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
            _append_line(
                log_path,
                f"{_now_ts()} - agent - INFO - TRACE_ARTIFACT_WRITTEN path={art_path}",
            )
        except Exception:
            pass
        return "file://" + art_path.replace("\\\\", "/")
    except Exception:
        try:
            log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
            _append_line(
                log_path,
                f"{_now_ts()} - agent - INFO - TRACE_ARTIFACT_FAILED req_id={req_id}",
            )
        except Exception:
            pass
        return None
        pass


def _log_streamlit_run(req_id: str, session_id: str | None = None) -> None:
    log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
    sid = session_id or ""
    msg = f"{_now_ts()} - agent - INFO - STREAMLIT_RUN req_id={req_id} session_id={sid}"
    _append_line(log_path, msg)


def _log_request_received(req_id: str, framework: str, path: str | None = None) -> None:
    log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
    p = path or ""
    msg = f"{_now_ts()} - agent - INFO - REQUEST_RECEIVED req_id={req_id} framework={framework} path={p}"
    _append_line(log_path, msg)


def _log_pinecone_query(req_id: str, customer_id: str | None, top_k: int | None, retrieved: int | None) -> None:
    log_path = os.environ.get("RAG_SERVICE_LOG_PATH", "rag_service.log")
    cust = customer_id or ""
    tk = top_k if top_k is not None else ""
    rc = retrieved if retrieved is not None else ""
    msg = (
        f"{_now_ts()} - agent - INFO - PINECONE_QUERY req_id={req_id} "
        f"customer_id={cust} top_k={tk} retrieved_chunks={rc}"
    )
    _append_line(log_path, msg)


def _log_databricks_query(req_id: str, table: str | None, predicate: str | None) -> None:
    log_path = os.environ.get("DB_QUERIES_LOG_PATH", "db_queries.log")
    tbl = table or ""
    pred = predicate or ""
    msg = f"DATABRICKS_QUERY req_id={req_id} table={tbl} predicate=\"{pred}\""
    _append_line(log_path, msg)

    artifact_ref = _write_local_artifact(
        req_id=req_id,
        payload={
            "ts": _now_ts(),
            "source": "databricks",
            "req_id": req_id,
            "db.sql.table": table,
            "db.sql.predicate": predicate,
        },
    )

    _append_trace_jsonl(
        {
            "ts": _now_ts(),
            "span": "rag.source_access",
            "rag.source.name": "databricks",
            "trace_id": None,
            "req_id": req_id,
            "db.sql.table": table,
            "db.sql.predicate": predicate,
            "artifact_ref": artifact_ref,
        }
    )


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


def _patch_pinecone() -> None:
    try:
        import pinecone  # type: ignore
    except Exception:
        return

    def _wrap_index_query(index_obj):  # type: ignore[no-untyped-def]
        orig_query = getattr(index_obj, "query", None)
        if not callable(orig_query):
            return
        if getattr(index_obj, "__vistora_query_patched__", False):
            return

        def query(*args, **kwargs):  # type: ignore[no-untyped-def]
            req_id = _get_req_id()
            top_k = kwargs.get("top_k")
            customer_id = _extract_customer_id_from_filter(kwargs.get("filter"))

            res = orig_query(*args, **kwargs)

            if req_id:
                retrieved = None
                try:
                    matches = getattr(res, "matches", None)
                    if matches is not None:
                        retrieved = len(matches)
                except Exception:
                    retrieved = None
                _log_pinecone_query(
                    req_id=req_id,
                    customer_id=customer_id,
                    top_k=top_k,
                    retrieved=retrieved,
                )

            return res

        try:
            setattr(index_obj, "query", query)
            setattr(index_obj, "__vistora_query_patched__", True)
        except Exception:
            # Some implementations may not allow attribute assignment; best-effort.
            pass

    # Pinecone v3 style: from pinecone import Pinecone; pc.Index(name)
    PineconeCls = getattr(pinecone, "Pinecone", None)
    if PineconeCls is not None and not getattr(PineconeCls, "__vistora_patched__", False):
        orig_index_factory = getattr(PineconeCls, "Index", None)
        if callable(orig_index_factory):

            def Index(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                idx = orig_index_factory(self, *args, **kwargs)
                _wrap_index_query(idx)
                return idx

            try:
                setattr(PineconeCls, "Index", Index)
                setattr(PineconeCls, "__vistora_patched__", True)
            except Exception:
                pass

    # Legacy style: from pinecone import Index
    IndexCls = getattr(pinecone, "Index", None)
    if IndexCls is not None and not getattr(IndexCls, "__vistora_patched__", False):
        orig_query = getattr(IndexCls, "query", None)
        if callable(orig_query):

            def query(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                req_id = _get_req_id()
                top_k = kwargs.get("top_k")
                customer_id = _extract_customer_id_from_filter(kwargs.get("filter"))

                res = orig_query(self, *args, **kwargs)

                if req_id:
                    retrieved = None
                    try:
                        matches = getattr(res, "matches", None)
                        if matches is not None:
                            retrieved = len(matches)
                    except Exception:
                        retrieved = None
                    _log_pinecone_query(
                        req_id=req_id,
                        customer_id=customer_id,
                        top_k=top_k,
                        retrieved=retrieved,
                    )

                return res

            try:
                setattr(IndexCls, "query", query)
                setattr(IndexCls, "__vistora_patched__", True)
            except Exception:
                pass


def _patch_databricks_sql() -> None:
    try:
        from databricks import sql  # type: ignore
    except Exception:
        return

    if getattr(sql, "__vistora_patched__", False):
        return

    orig_connect = getattr(sql, "connect", None)
    if not callable(orig_connect):
        return

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

                out = (
                    self._inner.execute(query, params)
                    if params is not None
                    else self._inner.execute(query)
                )

                if req_id:
                    _log_databricks_query(req_id=req_id, table=table, predicate=predicate)

                return out

            def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
                return getattr(self._inner, name)

        def cursor(*c_args, **c_kwargs):  # type: ignore[no-untyped-def]
            cur = orig_cursor(*c_args, **c_kwargs)
            return _CursorProxy(cur)

        setattr(conn, "cursor", cursor)
        return conn

    setattr(sql, "connect", connect)
    setattr(sql, "__vistora_patched__", True)


def _normalize_header_val(v: Any) -> str | None:
    try:
        if v is None:
            return None
        s = str(v).strip()
        return s or None
    except Exception:
        return None


def _new_req_id() -> str:
    return uuid.uuid4().hex


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


def _patch_asgi_req_id() -> None:
    """Best-effort per-request req_id injection for ASGI apps (Starlette/FastAPI).

    Wraps Starlette.__call__ so each request scope sets a ContextVar req_id.
    """
    try:
        from starlette.applications import Starlette  # type: ignore
    except Exception:
        return

    if getattr(Starlette, "__vistora_reqid_patched__", False):
        return

    orig_call = getattr(Starlette, "__call__", None)
    if not callable(orig_call):
        return

    async def __call__(self, scope, receive, send):  # type: ignore[no-untyped-def]
        if scope and scope.get("type") == "http":
            incoming = _req_id_from_asgi_scope(scope)
            req_id = incoming or _new_req_id()
            token = _REQ_ID_CVAR.set(req_id)
            try:
                _log_request_received(req_id=req_id, framework="asgi", path=str(scope.get("path") or ""))
                return await orig_call(self, scope, receive, send)
            finally:
                try:
                    _REQ_ID_CVAR.reset(token)
                except Exception:
                    pass
        return await orig_call(self, scope, receive, send)

    try:
        setattr(Starlette, "__call__", __call__)
        setattr(Starlette, "__vistora_reqid_patched__", True)
    except Exception:
        pass


def _patch_flask_req_id() -> None:
    """Best-effort per-request req_id injection for Flask (WSGI) apps."""
    try:
        from flask.app import Flask  # type: ignore
    except Exception:
        return

    if getattr(Flask, "__vistora_reqid_patched__", False):
        return

    orig_wsgi_app = getattr(Flask, "wsgi_app", None)
    if not callable(orig_wsgi_app):
        return

    def wsgi_app(self, environ, start_response):  # type: ignore[no-untyped-def]
        incoming = _req_id_from_wsgi_environ(environ)
        req_id = incoming or _new_req_id()
        token = _REQ_ID_CVAR.set(req_id)
        try:
            path = None
            try:
                path = environ.get("PATH_INFO")
            except Exception:
                path = None
            _log_request_received(req_id=req_id, framework="flask", path=path)
            return orig_wsgi_app(self, environ, start_response)
        finally:
            try:
                _REQ_ID_CVAR.reset(token)
            except Exception:
                pass

    try:
        setattr(Flask, "wsgi_app", wsgi_app)
        setattr(Flask, "__vistora_reqid_patched__", True)
    except Exception:
        pass


def _patch_django_req_id() -> None:
    """Best-effort per-request req_id injection for Django apps.

    Wraps BaseHandler.get_response which sits at the core request handling.
    """
    try:
        from django.core.handlers.base import BaseHandler  # type: ignore
    except Exception:
        return

    if getattr(BaseHandler, "__vistora_reqid_patched__", False):
        return

    orig_get_response = getattr(BaseHandler, "get_response", None)
    if not callable(orig_get_response):
        return

    def get_response(self, request):  # type: ignore[no-untyped-def]
        incoming = None
        try:
            incoming = request.headers.get("X-Request-ID")
        except Exception:
            try:
                incoming = getattr(request, "META", {}).get("HTTP_X_REQUEST_ID")
            except Exception:
                incoming = None
        req_id = _normalize_header_val(incoming) or _new_req_id()
        token = _REQ_ID_CVAR.set(req_id)
        try:
            path = None
            try:
                path = getattr(request, "path", None)
            except Exception:
                path = None
            _log_request_received(req_id=req_id, framework="django", path=path)
            return orig_get_response(self, request)
        finally:
            try:
                _REQ_ID_CVAR.reset(token)
            except Exception:
                pass

    try:
        setattr(BaseHandler, "get_response", get_response)
        setattr(BaseHandler, "__vistora_reqid_patched__", True)
    except Exception:
        pass


def _patch_streamlit_req_id() -> None:
    """Generate a fresh req_id per Streamlit rerun without customer code changes.

    We patch Streamlit's ScriptRunner._run_script so every rerun has a unique req_id
    stored in a ContextVar. Pinecone/Databricks hooks then pick it up.
    """
    try:
        from streamlit.runtime.scriptrunner.script_runner import ScriptRunner  # type: ignore
    except Exception:
        return

    if getattr(ScriptRunner, "__vistora_patched__", False):
        return

    orig_run_script = getattr(ScriptRunner, "_run_script", None)
    if not callable(orig_run_script):
        return

    def _run_script(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        # One req_id per rerun
        new_req_id = uuid.uuid4().hex
        token = _REQ_ID_CVAR.set(new_req_id)

        session_id = None
        try:
            # Best-effort: internal APIs vary across Streamlit versions
            session_id = getattr(getattr(self, "_session_info", None), "session_id", None)
        except Exception:
            session_id = None

        _log_streamlit_run(req_id=new_req_id, session_id=session_id)
        try:
            return orig_run_script(self, *args, **kwargs)
        finally:
            try:
                _REQ_ID_CVAR.reset(token)
            except Exception:
                pass

    setattr(ScriptRunner, "_run_script", _run_script)
    setattr(ScriptRunner, "__vistora_patched__", True)


def patch_all() -> None:
    _patch_asgi_req_id()
    _patch_flask_req_id()
    _patch_django_req_id()
    _patch_streamlit_req_id()
    _patch_pinecone()
    _patch_databricks_sql()
