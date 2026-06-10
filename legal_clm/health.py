from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.conf import settings


def healthz(request):
    checks = {
        "database": False,
        "redis": False,
    }

    # Database check
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = True
    except OperationalError:
        checks["database"] = False

    # Redis check using Celery broker URL if configured.
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    try:
        if broker_url.startswith("redis://"):
            import redis

            redis.Redis.from_url(broker_url, socket_connect_timeout=2, socket_timeout=2).ping()
            checks["redis"] = True
    except Exception:
        checks["redis"] = False

    healthy = all(checks.values())
    status = 200 if healthy else 503

    return JsonResponse(
        {
            "status": "ok" if healthy else "degraded",
            "checks": checks,
        },
        status=status,
    )
