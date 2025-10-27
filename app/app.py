from flask import Flask, request
import logging
import time
from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# Prometheus Metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['endpoint'])

# Tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(agent_host_name='jaeger', agent_port=6831)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))
tracer = trace.get_tracer(__name__)

@app.route('/')
def home():
    start = time.time()
    logging.info("Home endpoint accessed")
    with tracer.start_as_current_span("home-endpoint"):
        time.sleep(0.2)
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    REQUEST_LATENCY.labels(endpoint='/').observe(time.time() - start)
    return "Hello, Observability!"

@app.route('/health')
def health():
    logging.info("Health check")
    return "OK", 200

if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics
    app.run(host='0.0.0.0', port=5000)
