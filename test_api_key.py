#!/usr/bin/env python3
"""
서울 지하철 API 키 테스트 스크립트

.env 파일에 설정된 API 키가 정상 작동하는지 확인합니다.
"""

import os
from dotenv import load_dotenv
from subway_api_client import SeoulSubwayAPIClient

# 환경변수 로드
load_dotenv()


def test_api_key():
    """API 키 유효성 검사"""
    print("="*60)
    print("🔑 서울 지하철 API 키 테스트")
    print("="*60)

    # API 키 확인
    api_key = os.getenv('SUBWAY_API_KEY')
    if not api_key:
        print("❌ 오류: SUBWAY_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일을 확인하세요.")
        return False

    if api_key == "여기에_발급받은_API_키를_입력하세요":
        print("❌ 오류: API 키를 아직 입력하지 않았습니다.")
        print("   https://data.seoul.go.kr에서 API 키를 발급받아 .env 파일에 입력하세요.")
        return False

    print(f"✓ API 키 발견: {api_key[:10]}... (총 {len(api_key)}자)")

    try:
        client = SeoulSubwayAPIClient()
        print("✓ API 클라이언트 생성 성공")

        # 테스트용 역명
        test_station = "신도림"
        print(f"\n🧪 테스트 호출: {test_station}역 실시간 도착정보 조회")

        result = client.get_realtime_arrival(test_station)

        if result['success']:
            print(f"✅ API 호출 성공!")
            print(f"   도착 예정 열차: {result['count']}대")

            if result['count'] > 0:
                print("\n📋 첫 번째 열차 정보:")
                train = result['data'][0]
                print(f"   - 열차번호: {train['train_no']}")
                print(f"   - 방면: {train['train_line_nm']}")
                print(f"   - 도착시간: {train['arrival_time']}초 ({train['arrival_time']//60}분 후)")
                print(f"   - 현재위치: {train['current_station']}")
                print(f"   - 메시지: {train['arrival_msg']}")
            else:
                print("   ⚠️  현재 도착 예정인 열차가 없습니다.")

            print("\n" + "="*60)
            print("🎉 API 키 테스트 완료!")
            print("   정상적으로 작동합니다.")
            print("="*60)
            return True

        else:
            print(f"❌ API 호출 실패: {result.get('message')}")
            if 'error' in result:
                print(f"   에러 상세: {result['error']}")

            # 일반적인 오류 해결 가이드
            print("\n💡 문제 해결 가이드:")
            print("   1. API 키가 정확한지 확인하세요.")
            print("   2. https://data.seoul.go.kr에서 '실시간 지하철 인증키'를 발급받았는지 확인하세요.")
            print("   3. 일반 인증키가 아닌 '실시간 지하철' 전용 인증키여야 합니다.")
            print("   4. 인증키 활성화에 시간이 걸릴 수 있습니다 (발급 후 몇 분 대기).")

            return False

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_api_key()
    exit(0 if success else 1)
