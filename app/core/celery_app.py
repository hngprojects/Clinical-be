from celery import Celery

EMAIL_QUEUE = "email"

celery_app = Celery("clinsights")

celery_app.conf.update(
	task_acks_late=True,
	worker_prefetch_multiplier=1,
	task_default_queue="default",
	task_routes={
		"app.tasks.email.*": {"queue": EMAIL_QUEUE},
	},
	include=["app.tasks.email"],
)


def configure_celery(**kwargs: object) -> None:  # noqa: ARG001
	"""Configure broker and result backend from settings.

	Idempotent — safe to call multiple times.
	Call once during app/worker startup before dispatching tasks.
	"""
	if celery_app.conf.broker_url:
		return
	from app.core.config import get_settings

	settings = get_settings()
	celery_app.conf.update(
		broker_url=settings.CELERY_BROKER_URL,
		result_backend=settings.CELERY_RESULT_BACKEND,
	)


celery_app.on_after_finalize.connect(configure_celery)
