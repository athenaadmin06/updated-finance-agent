from typing import Any
import os
import json as _json

from dotenv import load_dotenv
from llama_index.llms.groq import Groq as GroqLLM
from llama_index.core.llms import CompletionResponse
from llama_index.core.llms.callbacks import llm_completion_callback

load_dotenv()


class TelemetryGroqLLM(GroqLLM):
    """
    Thin wrapper around llama-index's built-in Groq integration.
    Delegates the actual API call to the parent class (Groq's OpenAI-compatible
    /chat/completions), but preserves the original OTel span + S3 artifact
    telemetry logic from the Azure ML wrapper, unchanged.

    Env vars:
      GROQ_API_KEY  - Groq API key
    """

    # ------------------------------------------------------------------ helpers
    def _bool_env(self, name: str, default: bool = False) -> bool:
        v = os.environ.get(name)
        if v is None:
            return default
        return v.strip().lower() in ("1", "true", "yes", "y", "on")

    def _scrub(self, s: str) -> str:
        if self._bool_env("VISTORA_ALLOW_SENSITIVE_LOGS", default=False):
            return s
        return "[REDACTED]"

    def _maybe_put_artifact(self, trace_id: str, suffix: str, body: str):
        if not self._bool_env("VISTORA_ENABLE_ARTIFACT_UPLOAD", default=False):
            return None
        try:
            from vistora_instrumentation.otel_s3_patch import _artifact_key, _s3_put_text  # type: ignore
            key = _artifact_key(trace_id, suffix, "json")
            return _s3_put_text(key, body, "application/json")
        except Exception:
            return None

    def _maybe_put_llm_jsonl(self, trace_id: str, body: str) -> None:
        if not self._bool_env("VISTORA_LLM_JSONL_EXPORT", default=False):
            return
        try:
            import time, uuid, boto3  # type: ignore
            bucket = (
                os.environ.get("S3_LLM_BUCKET")
                or os.environ.get("S3_LOGS_BUCKET")
                or os.environ.get("S3_ARTIFACTS_BUCKET")
                or ""
            ).strip()
            if not bucket:
                return
            prefix = (os.environ.get("S3_LLM_PREFIX") or "llm").strip().strip("/")
            date_path = time.strftime("%Y/%m/%d", time.gmtime())
            ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            key = f"{prefix}/{date_path}/llm_{trace_id}_{ts}_{uuid.uuid4().hex}.jsonl"
            region = (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "").strip() or None
            s3 = boto3.client("s3", region_name=region)
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=(body.strip() + "\n").encode("utf-8"),
                ContentType="application/x-jsonlines",
            )
        except Exception:
            return

    # ------------------------------------------------------------------ core
    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        # Safety cap — qwen3.6-27b has a 131k token context window, so this is
        # generous headroom rather than a tight Azure-ML-style limit.
        MAX_PROMPT_CHARS = 60000
        if len(prompt) > MAX_PROMPT_CHARS:
            print(f"[TelemetryGroqLLM] Prompt truncated from {len(prompt)} -> {MAX_PROMPT_CHARS} chars")
            prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n[...truncated for length...]"

        tracer = None
        span = None
        try:
            from opentelemetry import trace  # type: ignore
            tracer = trace.get_tracer("vistora.llm")
        except Exception:
            tracer = None

        try:
            if tracer is not None:
                span = tracer.start_span("rag.llm")
                try:
                    span.set_attribute("rag.source.name", "groq_llm")
                    span.set_attribute("llm.provider", "groq")
                    span.set_attribute("llm.model", self.model)
                    try:
                        from vistora_instrumentation.otel_s3_patch import _get_agent_id, _get_req_id  # type: ignore
                        agent_id = _get_agent_id()
                        if agent_id:
                            span.set_attribute("vistora.agent_id", agent_id)
                        req_id = _get_req_id()
                        if req_id:
                            span.set_attribute("vistora.req_id", req_id)
                    except Exception:
                        pass
                except Exception:
                    pass

            try:
                response = super().complete(prompt, **kwargs)
                clean_text = response.text
            except Exception as e:
                print(f"Groq API Error: {e}")
                try:
                    if span is not None:
                        from opentelemetry import trace  # type: ignore
                        span.record_exception(e)
                        span.set_status(trace.status.Status(trace.status.StatusCode.ERROR))  # type: ignore[attr-defined]
                        ctx = span.get_span_context()
                        trace_id = format(getattr(ctx, "trace_id", 0) or 0, "032x")
                        err_payload = {
                            "type": "llm_error",
                            "provider": "groq",
                            "model": self.model,
                            "error": str(e),
                            "prompt": self._scrub(prompt),
                        }
                        err_uri = self._maybe_put_artifact(
                            trace_id, "llm_error", _json.dumps(err_payload, ensure_ascii=False, default=str)
                        )
                        if err_uri:
                            from vistora_instrumentation.otel_s3_patch import _emit_artifact_written  # type: ignore
                            _emit_artifact_written(span, data_platform="groq_llm", artifact_uri=err_uri, artifact_type="json")
                        self._maybe_put_llm_jsonl(
                            trace_id,
                            _json.dumps(
                                {"event": "llm.response", "status": "exception", "trace_id": trace_id, "model": self.model, "error": str(e)},
                                ensure_ascii=False, default=str,
                            ),
                        )
                except Exception:
                    pass
                return CompletionResponse(text=f"Connection Error: {str(e)}")

            # Emit telemetry artifacts
            try:
                if span is not None:
                    ctx = span.get_span_context()
                    trace_id = format(getattr(ctx, "trace_id", 0) or 0, "032x")

                    prompt_payload = {"type": "llm_prompt", "provider": "groq", "model": self.model, "prompt": self._scrub(prompt)}
                    resp_payload = {"type": "llm_response", "provider": "groq", "model": self.model, "response": self._scrub(clean_text)}

                    prompt_uri = self._maybe_put_artifact(trace_id, "llm_prompt", _json.dumps(prompt_payload, ensure_ascii=False, default=str))
                    if prompt_uri:
                        from vistora_instrumentation.otel_s3_patch import _emit_artifact_written  # type: ignore
                        _emit_artifact_written(span, data_platform="groq_llm", artifact_uri=prompt_uri, artifact_type="json")

                    resp_uri = self._maybe_put_artifact(trace_id, "llm_response", _json.dumps(resp_payload, ensure_ascii=False, default=str))
                    if resp_uri:
                        from vistora_instrumentation.otel_s3_patch import _emit_artifact_written  # type: ignore
                        _emit_artifact_written(span, data_platform="groq_llm", artifact_uri=resp_uri, artifact_type="json")

                    self._maybe_put_llm_jsonl(
                        trace_id,
                        _json.dumps({"event": "llm.request", "trace_id": trace_id, "model": self.model, "prompt": self._scrub(prompt)}, ensure_ascii=False, default=str),
                    )
                    self._maybe_put_llm_jsonl(
                        trace_id,
                        _json.dumps(
                            {"event": "llm.response", "status": "success", "trace_id": trace_id, "model": self.model, "response": self._scrub(clean_text)},
                            ensure_ascii=False, default=str,
                        ),
                    )
            except Exception:
                pass

            return response

        finally:
            try:
                if span is not None:
                    span.end()
            except Exception:
                pass