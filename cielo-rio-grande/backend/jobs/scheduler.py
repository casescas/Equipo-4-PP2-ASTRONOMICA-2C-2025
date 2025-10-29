from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import logging

from jobs.tasks import predict_octas

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

TZ = timezone("America/Argentina/Buenos_Aires")
scheduler = BackgroundScheduler(timezone=TZ)


def start_scheduler():
    trigger = CronTrigger(minute="3-59/10", second=0, timezone=TZ)  # 03,13,23,33,43,53
    scheduler.add_job(
        predict_octas,
        trigger=trigger,
        id="predict_octas_10min",
        max_instances=1,
        coalesce=True,
        replace_existing=False,
    )
    scheduler.start()
    logging.info("✅ Scheduler iniciado (intervalo: 5 segundos)")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logging.info("🛑 Scheduler detenido")
