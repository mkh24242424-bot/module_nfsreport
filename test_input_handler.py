"""input_handler 테스트 실행 스크립트"""

from module.input_handler import get_comparison_case_input

if __name__ == "__main__":
    scas, date, nfs_number = get_comparison_case_input()

    print("\n=== 입력 결과 ===")
    print(f"SCAS 접수번호: {scas}")
    print(f"접수 날짜: {date}")
    print(f"국과수 접수번호: {nfs_number}")
