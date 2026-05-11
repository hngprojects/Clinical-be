from celery import Celery

from app.core.config import get_settings

EMAIL_QUEUE = "email"


def create_celery_app() -> Celery:
	settings = get_settings()
	app = Celery(
		"clinsights",
		broker=settings.CELERY_BROKER_URL,
		backend=settings.CELERY_RESULT_BACKEND,
		include=["app.tasks.email"],
	)
	app.conf.update(
		task_acks_late=True,
		worker_prefetch_multiplier=1,
		task_default_queue="default",
		task_routes={
			"app.tasks.email.*": {"queue": EMAIL_QUEUE},
		},
	)
	return app


celery_app = create_celery_app()
