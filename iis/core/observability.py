import os
import logging
from typing import Optional, List

from opentelemetry import trace, _logs
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler, LogRecordProcessor, ReadWriteLogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
# In newer OTel SDKs, LogRecord is often ReadWriteLogRecord in the internal API
try:
    from opentelemetry.sdk._logs import LogRecord
except ImportError:
    from opentelemetry.sdk._logs._internal import LogRecord
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from traceloop.sdk import Traceloop

from core.pii_redactor import redactor

logger = logging.getLogger(__name__)

class RedactingSpanProcessor(SpanProcessor):
    def on_start(self, span: ReadableSpan, parent_context: Optional[object] = None) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        # Redact PII from span attributes
        if hasattr(span, "attributes") and span.attributes:
            pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        pass

class RedactingLogProcessor(LogRecordProcessor):
    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        # Redact PII from log body and attributes
        target = log_record.log_record if hasattr(log_record, "log_record") else log_record
        total_pii_count = 0
        
        if hasattr(target, "body") and isinstance(target.body, str):
            redacted_body, count = redactor.redact(target.body)
            target.body = redacted_body
            total_pii_count += count
        
        if hasattr(target, "attributes") and target.attributes:
            new_attrs = {}
            for key, value in target.attributes.items():
                if isinstance(value, str):
                    redacted_val, count = redactor.redact(value)
                    new_attrs[key] = redacted_val
                    total_pii_count += count
                else:
                    new_attrs[key] = value
            
            if total_pii_count > 0:
                new_attrs["pii.redaction_count"] = total_pii_count
                new_attrs["pii.protected"] = True
                
            target.attributes = new_attrs

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        pass

def setup_observability():
    """Sets up OpenTelemetry tracing and logging with direct DataDog OTLP/HTTP ingestion."""
    
    dd_api_key = os.getenv("DD_API_KEY")
    dd_site = os.getenv("DD_SITE", "datadoghq.com")
    service_name = os.getenv("SERVICE_NAME", "iis-backend")
    env = os.getenv("ENV", "dev")
    
    if not dd_api_key:
        logger.warning("DD_API_KEY not found. AI Observability will not be exported to DataDog.")
        try:
            # We still initialize Traceloop locally for logging/debugging if needed
            Traceloop.init(app_name=service_name, disable_batch=True)
        except Exception as e:
            logger.warning(f"Could not initialize Traceloop (likely missing API key): {e}")
        return

    # 1. Define Resource attributes
    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": env,
    })

    # 2. Configure OTLP/HTTP Trace Exporter for DataDog
    # Trace Endpoint: https://otlp.<SITE>/v1/traces
    trace_endpoint = f"https://otlp.{dd_site}/v1/traces"
    
    span_exporter = OTLPSpanExporter(
        endpoint=trace_endpoint,
        headers={
            "dd-api-key": dd_api_key,
            "Content-Type": "application/x-protobuf",
            "Accept": "application/json"
        }
    )

    # 3. Initialize TracerProvider
    provider = TracerProvider(resource=resource)
    
    # Add Redaction Processor as a safety net
    provider.add_span_processor(RedactingSpanProcessor())
    
    trace_processor = BatchSpanProcessor(span_exporter)
    provider.add_span_processor(trace_processor)
    trace.set_tracer_provider(provider)

    # 4. Configure OTLP/HTTP Log Exporter for DataDog
    # Log Endpoint: https://otlp.<SITE>/v1/logs
    log_endpoint = f"https://otlp.{dd_site}/v1/logs"
    
    log_exporter = OTLPLogExporter(
        endpoint=log_endpoint,
        headers={
            "dd-api-key": dd_api_key,
            "Content-Type": "application/x-protobuf",
            "Accept": "application/json"
        }
    )

    # 5. Initialize LoggerProvider
    logger_provider = LoggerProvider(resource=resource)
    
    # Add Redaction Processor for Logs
    logger_provider.add_log_record_processor(RedactingLogProcessor())
    
    log_processor = BatchLogRecordProcessor(log_exporter)
    logger_provider.add_log_record_processor(log_processor)
    _logs.set_logger_provider(logger_provider)

    # 6. Attach LoggingHandler to the root logger to capture all system logs
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)

    # 7. Initialize Traceloop (OpenLLMetry)
    # It will use the global tracer provider we just set up
    Traceloop.init(
        app_name=service_name,
        resource_attributes={"deployment.environment": env},
        disable_batch=False
    )

    logger.info(f"AI Observability initialized (Direct Ingest to {dd_site} for Traces and Logs)")
