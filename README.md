# 서울 지하철 실시간 추적 시스템

서울 열린데이터 광장의 실시간 지하철 API를 활용하여 지하철 열차의 실시간 위치를 추적하는 Celery 기반 시스템입니다.

## 주요 기능

- **실시간 도착정보 조회**: 특정 역에 도착 예정인 열차 정보
- **실시간 위치정보 조회**: 특정 호선의 모든 열차 위치
- **자동 추적**: Celery Beat를 통한 주기적 데이터 수집 (30초마다)
- **Docker 기반**: RabbitMQ와 함께 간편한 배포 및 실행

## 시스템 구조

```
seoul-subway-data/
├── subway_api_client.py    # 서울 지하철 API 클라이언트
├── celery_config.py        # Celery 설정 및 Beat 스케줄
├── tasks.py                # Celery 작업 정의
├── docker-compose.yml      # Docker Compose 설정
├── Dockerfile              # Docker 이미지 빌드
├── requirements.txt        # Python 의존성
├── .env.example            # 환경 변수 예시
├── test_api_key.py         # API 키 테스트 스크립트
├── find_station.py         # 역 검색 도구
└── logs/                   # 수집된 데이터 로그
    └── subway_data_log.json
```

## 빠른 시작

### 1. API 키 발급

1. [서울 열린데이터 광장](https://data.seoul.go.kr) 회원가입
2. 로그인 후 **인증키 신청**
3. **"실시간 지하철 인증키"** 신청 (필수!)
   - 일반 인증키가 아닌 **실시간 지하철 전용 인증키**를 발급받아야 합니다
4. 발급받은 인증키를 `.env` 파일에 입력

### 2. 환경 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집하여 API 키 입력
# SUBWAY_API_KEY=발급받은_API_키_입력
```

### 3. Docker로 실행

```bash
# Docker 이미지 빌드 및 전체 시스템 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f celery-worker
```

### 4. API 키 테스트 (선택)

```bash
# 가상환경 생성 (로컬 테스트용)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 패키지 설치
pip install -r requirements.txt

# API 키 테스트
python test_api_key.py
```

## 사용 방법

### 1. 특정 역 조회 (로컬)

```bash
# 신도림역 전체 노선 조회
python find_station.py 신도림

# 신도림역 2호선만 조회
python find_station.py 신도림 1002
```

### 2. Docker로 자동 추적

Docker Compose를 실행하면 다음과 같이 동작합니다:

1. **RabbitMQ** 컨테이너가 메시지 브로커로 실행
2. **Celery Worker** 컨테이너가 작업 처리
3. **Celery Beat** 컨테이너가 30초마다 자동으로 지하철 추적 작업 실행

```bash
# 전체 시스템 실행
docker-compose up --build

# 특정 서비스만 실행
docker-compose up rabbitmq celery-worker

# 중지
docker-compose down
```

### 3. 로그 확인

수집된 데이터는 `logs/subway_data_log.json` 파일에 저장됩니다.

```bash
# 실시간 로그 확인 (Linux/Mac)
tail -f logs/subway_data_log.json

# Docker 로그 확인
docker-compose logs -f celery-worker
```

## 환경 변수 설정

| 변수 | 설명 | 예시 |
|------|------|------|
| `SUBWAY_API_KEY` | 서울 지하철 API 키 (필수) | `발급받은_키` |
| `STATION_NAME` | 추적할 역명 | `신도림` |
| `LINE_NUM` | 호선 번호 | `1002` (2호선) |
| `RABBITMQ_HOST` | RabbitMQ 호스트 | `localhost` |
| `RABBITMQ_PORT` | RabbitMQ 포트 | `5672` |

### 호선 번호 목록

| 호선 번호 | 호선명 |
|----------|--------|
| 1001 | 1호선 |
| 1002 | 2호선 |
| 1003 | 3호선 |
| 1004 | 4호선 |
| 1005 | 5호선 |
| 1006 | 6호선 |
| 1007 | 7호선 |
| 1008 | 8호선 |
| 1009 | 9호선 |
| 1063 | 경의중앙선 |
| 1065 | 공항철도 |
| 1067 | 경춘선 |
| 1075 | 수인분당선 |
| 1077 | 신분당선 |

## API 클라이언트 사용 예시

```python
from subway_api_client import SeoulSubwayAPIClient

# 클라이언트 생성
client = SeoulSubwayAPIClient()

# 1. 실시간 도착정보 조회
result = client.get_realtime_arrival("신도림")

if result['success']:
    for train in result['data']:
        print(f"열차: {train['train_no']}")
        print(f"도착시간: {train['arrival_time']}초 후")
        print(f"현재위치: {train['current_station']}")

# 2. 특정 역 추적 (호선 필터링)
result = client.track_train_to_station(
    station_name="신도림",
    line_num="1002"  # 2호선만
)

# 3. 호선 전체 위치정보 조회
result = client.get_realtime_position("2호선")

if result['success']:
    print(f"운행 중인 열차: {result['count']}대")
```

## 기술 스택

- **Python 3.12**
- **Celery 5.3.4** - 분산 작업 큐
- **RabbitMQ** - 메시지 브로커
- **Docker & Docker Compose** - 컨테이너화
- **Requests** - HTTP 클라이언트
- **python-dotenv** - 환경 변수 관리

## 문제 해결

### API 키 오류

```
❌ API 에러 (ERROR-338): 해당 인증키로는 실시간 서비스를 사용할 수 없습니다.
```

**해결 방법:**
1. `.env` 파일에 올바른 API 키가 입력되었는지 확인
2. **실시간 지하철 인증키**를 발급받았는지 확인 (일반 인증키와 다름!)
3. 서울 열린데이터 광장에서 "실시간 지하철" 전용 인증키를 별도로 신청
4. API 키 활성화에 몇 분이 걸릴 수 있음

### RabbitMQ 연결 오류

```
❌ Error: [Errno 111] Connection refused
```

**해결 방법:**
1. RabbitMQ가 실행 중인지 확인: `docker-compose ps`
2. RabbitMQ 관리 콘솔 확인: http://localhost:15672 (guest/guest)
3. 포트 충돌 확인: `docker-compose down` 후 재시작

### 데이터가 안 나올 때

- API 키가 `sample`이면 최대 5건까지만 조회 가능
- 정식 인증키를 발급받아야 전체 데이터 조회 가능
- **심야 시간대(자정~새벽 5시)**에는 운행하는 열차가 없음

### 코드 변경 후 반영 안 될 때

```bash
# Docker 이미지를 재빌드해야 합니다
docker-compose down
docker-compose up --build
```

`--build` 플래그를 꼭 추가해야 변경된 코드가 반영됩니다!

## had-better 프로젝트 연동

이 시스템은 `had-better` 프로젝트의 실시간 지하철 경주 기능을 위해 개발되었습니다.

### 연동 방법

**1. Celery 작업 호출**

```python
# had-better 백엔드에서
from tasks import fetch_subway_arrival_info

# 비동기 작업 실행
task = fetch_subway_arrival_info.delay(
    station_name="신도림",
    line_num="1002"
)

# 결과 확인
result = task.get(timeout=10)
```

**2. 직접 API 호출**

```python
# had-better 백엔드에서
from subway_api_client import SeoulSubwayAPIClient

client = SeoulSubwayAPIClient()
trains = client.track_train_to_station("신도림", "1002")
```

## 라이선스

MIT License

## 문의

이슈가 있으면 GitHub Issues에 등록해주세요.
