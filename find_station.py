#!/usr/bin/env python3
"""
지하철역 검색 도구

원하는 역명의 실시간 정보를 조회하는 스크립트
"""

import sys
from dotenv import load_dotenv
from subway_api_client import SeoulSubwayAPIClient

load_dotenv()


def search_station(station_name: str, line_num: str = None):
    """
    역명으로 실시간 도착정보 검색

    Args:
        station_name: 역명 (예: "신도림", "홍대입구")
        line_num: 호선 번호 (선택, 예: "1002")
    """
    print("="*80)
    print(f"🔍 {station_name}역 실시간 도착정보 조회")
    if line_num:
        print(f"   호선 필터: {line_num}")
    print("="*80)

    try:
        client = SeoulSubwayAPIClient()

        result = client.track_train_to_station(
            station_name=station_name,
            line_num=line_num
        )

        if not result['success']:
            print(f"❌ 조회 실패: {result.get('message')}")
            return

        if result['count'] == 0:
            print(f"⚠️  {station_name}역에 도착 예정인 열차가 없습니다.")
            return

        print(f"\n✅ 도착 예정 열차: {result['count']}대\n")

        for idx, train in enumerate(result['data'], 1):
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"🚇 [{idx}번째 열차]")
            print(f"   열차번호: {train['train_no']}")
            print(f"   호선: {train['subway_nm']} ({train['subway_id']})")
            print(f"   방면: {train['train_line_nm']}")
            print(f"   도착시간: {train['arrival_time']}초 ({train['arrival_time']//60}분 {train['arrival_time']%60}초 후)")
            print(f"   도착메시지: {train['arrival_msg']}")
            print(f"   현재위치: {train['current_station']}")
            print(f"   상태: {_get_status_text(train['status'])}")

            # 특수 정보
            tags = []
            if train['is_express']:
                tags.append("🚄 급행")
            if train['is_last_train']:
                tags.append("🌙 막차")
            if tags:
                print(f"   특이사항: {', '.join(tags)}")

        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")


def _get_status_text(status_code: str) -> str:
    """상태 코드를 텍스트로 변환"""
    status_map = {
        '0': '진입',
        '1': '도착',
        '2': '출발',
        '3': '전역출발',
        '4': '전역진입',
        '5': '전역도착',
    }
    return status_map.get(status_code, f'알 수 없음({status_code})')


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python find_station.py <역명> [호선번호]")
        print("\n예시:")
        print("  python find_station.py 신도림")
        print("  python find_station.py 신도림 1002")
        print("\n호선 번호:")
        print("  1001: 1호선")
        print("  1002: 2호선")
        print("  1003: 3호선")
        print("  ...")
        sys.exit(1)

    station_name = sys.argv[1]
    line_num = sys.argv[2] if len(sys.argv) > 2 else None

    search_station(station_name, line_num)


if __name__ == "__main__":
    main()
