import logging

from celery import Task

log = logging.getLogger(__name__)


class BaseTask(Task):
    """Base Celery Task with sane defaults.

    - Retries with exponential backoff + jitter
    - Logs success/failure events
    """

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    max_retries = 5

    def on_success(self, retval, task_id, args, kwargs):
        """Log successful completion of a Celery task."""
        log.info(
            {
                "msg": "celery_success",
                "task": self.name,
                "task_id": task_id,
            }
        )
        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log failure details when a Celery task raises an exception."""
        log.error(
            {
                "msg": "celery_failure",
                "task": self.name,
                "task_id": task_id,
                "error": str(exc),
            }
        )
        return super().on_failure(exc, task_id, args, kwargs, einfo)
