import os
import json
from datetime import datetime
from celery_config import app
from subway_api_client import SeoulSubwayAPIClient
from dotenv import load_dotenv

load_dotenv()


@app.task(bind=True, name='tasks.fetch_subway_arrival_info')
def fetch_subway_arrival_info(self, station_name: str = None, line_num: str = None):
    """
    지하철 도착 정보를 외부 API에서 가져오는 Celery 태스크

    Args:
        station_name: 역명 (환경변수에서 가져옴)
        line_num: 호선 번호 (환경변수에서 가져옴)

    Returns:
        처리 결과 딕셔너리
    """
    print(f"[{datetime.now()}] 지하철 도착 정보 수집 시작 - Task ID: {self.request.id}")

    try:
        # API 클라이언트 초기화
        client = SeoulSubwayAPIClient()

        # 환경변수에서 설정 가져오기
        station_name = station_name or os.getenv('STATION_NAME', '신도림')
        line_num = line_num or os.getenv('LINE_NUM')

        if not station_name:
            raise ValueError("STATION_NAME이 설정되지 않았습니다.")

        # API 호출
        result = client.track_train_to_station(
            station_name=station_name,
            line_num=line_num
        )

        if result['success']:
            print(f"✓ 성공: {result['count']}개의 열차 정보 수집")

            # 수집된 데이터 로깅
            for train in result['data']:
                print(f"\n  === {train['train_no']} - {train['train_line_nm']} ===")
                print(f"  역: {train['station_nm']}")
                print(f"  도착 예정: {train['arrival_time']}초 ({train['arrival_time']//60}분 {train['arrival_time']%60}초)")
                print(f"  도착 메시지: {train['arrival_msg']}")
                print(f"  현재 위치: {train['current_station']}")
                print(f"  막차 여부: {'막차' if train['is_last_train'] else '일반'}")
                print(f"  급행 여부: {'급행' if train['is_express'] else '완행'}")

            # 데이터 처리 (로그 저장)
            process_subway_data(result['data'])

            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data_count': result['count'],
                'task_id': self.request.id
            }
        else:
            print(f"✗ 실패: {result.get('message', 'Unknown error')}")
            return {
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': result.get('message'),
                'task_id': self.request.id
            }

    except Exception as e:
        print(f"✗ 예외 발생: {str(e)}")
        # Celery의 자동 재시도 기능 활용
        raise self.retry(exc=e, countdown=60, max_retries=3)


def process_subway_data(subway_data_list):
    """
    수집된 지하철 데이터 처리 함수

    실제 프로젝트에서는 여기에 다음과 같은 로직이 들어갈 수 있습니다:
    - 데이터베이스 저장
    - 캐시 업데이트
    - SSE로 클라이언트에 실시간 전송
    - 특정 조건 만족 시 알림 발송
    """
    # 데모용 로그 저장
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'subway_data_log.json')

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'data': subway_data_list
    }

    # 기존 로그 읽기
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    # 새 로그 추가 (최근 100개만 유지)
    logs.append(log_entry)
    logs = logs[-100:]

    # 로그 저장
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"  → 데이터 처리 완료: {log_file}에 저장됨")


@app.task(bind=True, name='tasks.fetch_subway_tracking_flow')
def fetch_subway_tracking_flow(self):
    """
    전체 지하철 추적 플로우를 실행하는 Celery 태스크

    1단계: 특정 역의 실시간 도착정보 조회
    2단계: 해당 노선의 실시간 위치정보 조회
    3단계: 열차 번호로 매칭하여 상세 위치 추적

    Returns:
        처리 결과 딕셔너리
    """
    print(f"\n{'='*80}")
    print(f"🚇 서울 지하철 실시간 추적 시스템 - Task ID: {self.request.id}")
    print(f"{'='*80}")

    try:
        client = SeoulSubwayAPIClient()

        # 환경변수에서 설정 가져오기
        station_name = os.getenv('STATION_NAME', '신도림')
        line_num = os.getenv('LINE_NUM')

        print(f"\n📍 추적 대상:")
        print(f"  - 역명: {station_name}")
        print(f"  - 호선: {line_num}")

        # ====== 1단계: 도착정보 조회 ======
        print(f"\n🔍 [1단계] 실시간 도착정보 조회 중...")
        arrival_result = client.track_train_to_station(
            station_name=station_name,
            line_num=line_num
        )

        if not arrival_result['success'] or arrival_result['count'] == 0:
            error_msg = arrival_result.get('message', '도착 정보를 찾을 수 없습니다')
            print(f"  ❌ 실패: {error_msg}")
            return {
                'status': 'failed',
                'stage': 'arrival_info',
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'task_id': self.request.id
            }

        trains = arrival_result['data']
        print(f"  ✅ 도착 정보 조회 성공: {len(trains)}대의 열차 발견")

        # ====== 2단계: 각 열차 정보 출력 ======
        print(f"\n🚇 [2단계] 열차별 상세 정보")
        print(f"{'─'*80}")

        all_train_data = []

        for idx, train in enumerate(trains[:5], 1):  # 최대 5개만 표시
            print(f"\n  [{idx}번째 열차]")
            print(f"     열차번호: {train['train_no']}")
            print(f"     방면: {train['train_line_nm']}")
            print(f"     도착시간: {train['arrival_time']}초 ({train['arrival_time']//60}분 {train['arrival_time']%60}초 후)")
            print(f"     도착메시지: {train['arrival_msg']}")
            print(f"     현재위치: {train['current_station']}")
            print(f"     상태: {_get_train_status_text(train['status'])}")

            if train['is_express']:
                print(f"     🚄 급행열차")
            if train['is_last_train']:
                print(f"     🌙 막차")

            all_train_data.append({
                'train_no': train['train_no'],
                'direction': train['direction'],
                'arrival_time': train['arrival_time'],
                'arrival_msg': train['arrival_msg'],
                'current_station': train['current_station'],
                'status': train['status'],
                'is_express': train['is_express'],
                'is_last_train': train['is_last_train'],
            })

        # ====== 3단계: 호선 전체 위치정보 조회 (선택적) ======
        line_name = _convert_line_num_to_name(line_num)
        if line_name:
            print(f"\n📍 [3단계] {line_name} 전체 열차 위치 조회 중...")
            position_result = client.get_realtime_position(line_name)

            if position_result['success'] and position_result['count'] > 0:
                print(f"  ✅ 위치 정보 조회 성공: {position_result['count']}대의 열차 운행 중")

                # 우리가 추적하는 열차들과 매칭
                tracked_train_nos = [t['train_no'] for t in all_train_data]
                for pos in position_result['data']:
                    if pos['train_no'] in tracked_train_nos:
                        print(f"     🎯 {pos['train_no']}: {pos['current_station']} → {pos['next_station']}")
            else:
                print(f"  ⚠️  위치 정보 조회 실패 또는 데이터 없음")

        print(f"\n{'='*80}")
        print(f"✨ 전체 프로세스 완료!")
        print(f"   → {len(all_train_data)}대의 열차를 추적하고 있습니다!")
        print(f"{'='*80}\n")

        # 전체 데이터를 로그에 저장
        full_tracking_data = {
            'station_name': station_name,
            'line_num': line_num,
            'trains': all_train_data
        }
        process_subway_data([full_tracking_data])

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'station_name': station_name,
            'train_count': len(all_train_data),
            'trains': all_train_data,
            'task_id': self.request.id
        }

    except Exception as e:
        print(f"✗ 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        # Celery의 자동 재시도 기능 활용
        raise self.retry(exc=e, countdown=60, max_retries=3)


def _get_train_status_text(status_code: str) -> str:
    """열차 상태 코드를 텍스트로 변환"""
    status_map = {
        '0': '진입',
        '1': '도착',
        '2': '출발',
        '3': '전역출발',
        '4': '전역진입',
        '5': '전역도착',
    }
    return status_map.get(status_code, f'알 수 없음({status_code})')


def _convert_line_num_to_name(line_num: str) -> str:
    """호선 번호를 호선명으로 변환"""
    line_map = {
        '1001': '1호선',
        '1002': '2호선',
        '1003': '3호선',
        '1004': '4호선',
        '1005': '5호선',
        '1006': '6호선',
        '1007': '7호선',
        '1008': '8호선',
        '1009': '9호선',
        '1063': '경의중앙선',
        '1065': '공항철도',
        '1067': '경춘선',
        '1075': '수인분당선',
        '1077': '신분당선',
    }
    return line_map.get(line_num, '')


@app.task(name='tasks.manual_trigger')
def manual_trigger():
    """
    수동으로 트리거할 수 있는 테스트 태스크
    """
    print(f"[{datetime.now()}] 수동 트리거 태스크 실행")
    return fetch_subway_arrival_info()
