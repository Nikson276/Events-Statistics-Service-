
• Full review comments:

  - [P1] Break circular import with router dependency — ess/app/routers/events.py:4-5
    The router imports get_kafka_service from ess.app.main, while main imports this router before get_kafka_service is defined. During startup main is only partially initialized when events.py executes from ess.app.main import get_kafka_service, so the attribute is missing and Python raises ImportError: cannot import name 'get_kafka_service' from partially initialized module 'ess.app.main'. This prevents the
  FastAPI app from even starting. The router should depend on get_kafka_service from ess.app.services.kafka (where the service actually lives) or otherwise break the circular import.
  - [P1] Kafka dependency never initialized — ess/app/main.py:24-41
    Even if the circular import were fixed, the dependency provided by ess.app.main.get_kafka_service can never succeed because the module-level kafka_service remains None. The lifespan hook calls init_kafka() from services.kafka, which initializes an internal _kafka_service, but main.get_kafka_service still checks its own kafka_service variable and always raises RuntimeError. As a result every request
  depending on Kafka (e.g., POST /events) will fail at runtime. Either assign the created producer to kafka_service in lifespan or, simpler, reuse services.kafka.get_kafka_service so that the router receives the started producer.
  