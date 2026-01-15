import os
from celery import Celery
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# RabbitMQ 설정
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', '5672')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')

# Celery 앱 생성
app = Celery(
    'subway_api_tasks',
    broker=f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}',
    backend='rpc://'
)

# Celery 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 주기적 작업 스케줄 설정 (Beat)
app.conf.beat_schedule = {
    'fetch-subway-tracking-every-30-seconds': {
        'task': 'tasks.fetch_subway_tracking_flow',
        'schedule': 30.0,  # 30초마다 실행
    },
}
