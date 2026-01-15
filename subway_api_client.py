import os
import requests
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()


class SeoulSubwayAPIClient:
    """서울 지하철 실시간 정보 API 클라이언트"""

    # 실시간 지하철 API 도메인
    BASE_URL = "http://swopenapi.seoul.go.kr/api/subway"

    def __init__(self):
        self.api_key = os.getenv('SUBWAY_API_KEY')
        if not self.api_key:
            raise ValueError("SUBWAY_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    def get_realtime_arrival(self, station_name: str, start_index: int = 0, end_index: int = 100) -> Dict:
        """
        특정 역의 실시간 도착정보 조회

        Args:
            station_name: 역명 (예: "신도림", "홍대입구")
            start_index: 시작 인덱스
            end_index: 종료 인덱스

        Returns:
            실시간 도착정보 응답 데이터
        """
        url = f"{self.BASE_URL}/{self.api_key}/json/realtimeStationArrival/{start_index}/{end_index}/{station_name}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 에러 체크 1: status 500 에러 확인 (ERROR-338 등)
            if "status" in data and data["status"] == 500:
                error_msg = data.get("message", "알 수 없는 에러")
                error_code = data.get("code", "")
                return {
                    'success': False,
                    'error': f"{error_code}: {error_msg}",
                    'message': f'API 에러 ({error_code}): {error_msg}'
                }

            # 에러 체크 2: errorMessage가 있고 status가 200이 아닌 경우
            if "errorMessage" in data:
                error_info = data["errorMessage"]
                # INFO-000은 정상 응답이므로 에러가 아님
                if error_info.get("code") != "INFO-000" and error_info.get("status") != 200:
                    error_msg = error_info.get("message", "알 수 없는 에러")
                    return {
                        'success': False,
                        'error': error_msg,
                        'message': f'API 에러: {error_msg}'
                    }

            # 정상 응답 파싱
            return self._parse_arrival_response(data)

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'API 요청 실패'
            }

    def _parse_arrival_response(self, data: Dict) -> Dict:
        """
        실시간 도착정보 응답 파싱

        Args:
            data: API 응답 데이터

        Returns:
            파싱된 데이터
        """
        try:
            arrival_list = data.get('realtimeArrivalList', [])

            parsed_data = []
            for train in arrival_list:
                parsed_data.append({
                    # 열차 정보
                    'train_no': train.get('trainNo', ''),  # 열차번호 (예: "2234")
                    'train_line_nm': train.get('trainLineNm', ''),  # 도착지 방면 (예: "성수행 - 외선순환")

                    # 노선 정보
                    'subway_id': train.get('subwayId', ''),  # 호선 ID (예: "1002" = 2호선)
                    'subway_nm': train.get('subwayNm', ''),  # 호선 이름

                    # 역 정보
                    'station_nm': train.get('statnNm', ''),  # 역명

                    # 도착 정보
                    'arrival_time': int(train.get('barvlDt', 0)),  # 도착 예정 시간(초)
                    'arrival_msg': train.get('arvlMsg2', ''),  # 도착 메시지 (예: "전역 출발")
                    'arrival_code': train.get('arvlCd', ''),  # 도착코드 (0:진입, 1:도착, 2:출발, 3:전역출발, 4:전역진입, 5:전역도착)

                    # 현재 위치
                    'current_station': train.get('arvlMsg3', ''),  # 현재 위치 (예: "성수")

                    # 방향 정보
                    'up_down': train.get('updnLine', ''),  # 상행/하행 (0:상행, 1:하행)
                    'direction': train.get('trainLineNm', '').split('-')[0].strip() if '-' in train.get('trainLineNm', '') else train.get('trainLineNm', ''),

                    # 기타 정보
                    'is_express': train.get('directAt', '0') == '1',  # 급행 여부
                    'is_last_train': train.get('lstcarAt', '0') == '1',  # 막차 여부
                    'status': train.get('trainSttus', ''),  # 열차상태 (0:진입, 1:도착, 2:출발, 3:전역출발)

                    # 시간 정보
                    'received_time': train.get('recptnDt', ''),  # 정보 수신 시간
                })

            return {
                'success': True,
                'count': len(parsed_data),
                'data': parsed_data
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '응답 파싱 실패'
            }

    def get_realtime_position(self, line_name: str, start_index: int = 0, end_index: int = 100) -> Dict:
        """
        특정 호선의 실시간 열차 위치 정보 조회

        Args:
            line_name: 호선명 (예: "2호선", "9호선")
            start_index: 시작 인덱스
            end_index: 종료 인덱스

        Returns:
            실시간 위치정보 응답 데이터
        """
        url = f"{self.BASE_URL}/{self.api_key}/json/realtimePosition/{start_index}/{end_index}/{line_name}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 에러 체크 1: status 500 에러 확인 (ERROR-338 등)
            if "status" in data and data["status"] == 500:
                error_msg = data.get("message", "알 수 없는 에러")
                error_code = data.get("code", "")
                return {
                    'success': False,
                    'error': f"{error_code}: {error_msg}",
                    'message': f'API 에러 ({error_code}): {error_msg}'
                }

            # 에러 체크 2: errorMessage가 있고 status가 200이 아닌 경우
            if "errorMessage" in data:
                error_info = data["errorMessage"]
                # INFO-000은 정상 응답이므로 에러가 아님
                if error_info.get("code") != "INFO-000" and error_info.get("status") != 200:
                    error_msg = error_info.get("message", "알 수 없는 에러")
                    return {
                        'success': False,
                        'error': error_msg,
                        'message': f'API 에러: {error_msg}'
                    }

            # 정상 응답 파싱
            return self._parse_position_response(data)

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'API 요청 실패'
            }

    def _parse_position_response(self, data: Dict) -> Dict:
        """
        실시간 위치정보 응답 파싱

        Args:
            data: API 응답 데이터

        Returns:
            파싱된 데이터
        """
        try:
            position_list = data.get('realtimePositionList', [])

            parsed_data = []
            for train in position_list:
                parsed_data.append({
                    # 열차 정보
                    'train_no': train.get('trainNo', ''),  # 열차번호
                    'train_status': train.get('trainSttus', ''),  # 상태 (0:진입, 1:도착, 2:출발, 3:전역출발)

                    # 위치 정보
                    'current_station': train.get('statnNm', ''),  # 현재 위치역
                    'next_station': train.get('statnTnm', ''),  # 다음역

                    # 방향 정보
                    'direction': train.get('trainLineNm', ''),  # 행선지 (예: "성수행 - 외선순환")
                    'up_down': train.get('updnLine', ''),  # 상행/하행

                    # 호선 정보
                    'subway_id': train.get('subwayId', ''),  # 호선 ID

                    # 시간 정보
                    'received_time': train.get('recptnDt', ''),  # 수신 시간
                })

            return {
                'success': True,
                'count': len(parsed_data),
                'data': parsed_data
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '응답 파싱 실패'
            }

    def track_train_to_station(
        self,
        station_name: str,
        line_num: Optional[str] = None,
        direction: Optional[str] = None
    ) -> Dict:
        """
        특정 역으로 오는 열차 추적

        Args:
            station_name: 역명 (예: "신도림")
            line_num: 호선 번호 (예: "1002" = 2호선) (선택)
            direction: 방향 (선택)

        Returns:
            도착 예정 열차 정보
        """
        # 1. 실시간 도착정보 조회
        arrival_result = self.get_realtime_arrival(station_name)

        if not arrival_result['success']:
            return arrival_result

        trains = arrival_result['data']

        # 2. 필터링
        if line_num:
            trains = [t for t in trains if t['subway_id'] == line_num]

        if direction:
            trains = [t for t in trains if direction in t['train_line_nm']]

        # 3. 도착 시간순 정렬
        trains.sort(key=lambda x: x['arrival_time'])

        return {
            'success': True,
            'count': len(trains),
            'station_name': station_name,
            'data': trains
        }
