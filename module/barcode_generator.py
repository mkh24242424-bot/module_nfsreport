"""
텍스트를 바코드 이미지로 변환하는 코드
"""

import barcode
from barcode.writer import ImageWriter
from PIL import Image
import os


def generate_barcode(text: str, filename: str = "barcode", barcode_type: str = "code128") -> str:
    """
    텍스트를 바코드 이미지로 변환하여 저장합니다.
    
    Args:
        text: 바코드로 변환할 텍스트
        filename: 저장할 파일명 (확장자 제외)
        barcode_type: 바코드 종류 (code128, code39, ean13 등)
    
    Returns:
        저장된 파일 경로
    """
    # 바코드 클래스 가져오기
    barcode_class = barcode.get_barcode_class(barcode_type)
    
    # ImageWriter 옵션 설정
    writer = ImageWriter()
    
    # 바코드 생성
    barcode_instance = barcode_class(text, writer=writer)
    
    # 이미지로 저장 (자동으로 .png 확장자 추가됨)
    saved_path = barcode_instance.save(filename, options={
        'module_width': 0.4,      # 바코드 선 두께
        'module_height': 15.0,    # 바코드 높이 (mm)
        'quiet_zone': 6.5,        # 좌우 여백
        'font_size': 10,          # 텍스트 폰트 크기
        'text_distance': 5.0,     # 바코드와 텍스트 간격
        'write_text': True,       # 바코드 아래 텍스트 표시
    })
    
    return saved_path


def generate_barcode_no_text(text: str, filename: str = "barcode", barcode_type: str = "code128") -> str:
    """
    텍스트 없이 바코드만 생성합니다 (업로드된 이미지처럼).
    """
    barcode_class = barcode.get_barcode_class(barcode_type)
    writer = ImageWriter()
    
    barcode_instance = barcode_class(text, writer=writer)
    
    saved_path = barcode_instance.save(filename, options={
        'module_width': 0.4,
        'module_height': 15.0,
        'quiet_zone': 2.0,
        'write_text': False,  # 텍스트 숨김
    })
    
    return saved_path


if __name__ == "__main__":
    # 예시: 텍스트를 바코드로 변환
    test_text = "HELLO12345"
    
    # 텍스트 포함 바코드 생성
    result1 = generate_barcode(test_text, "barcode_with_text")
    print(f"텍스트 포함 바코드 저장됨: {result1}")
    
    # 텍스트 없는 바코드 생성 (업로드된 이미지 스타일)
    result2 = generate_barcode_no_text(test_text, "barcode_no_text")
    print(f"텍스트 없는 바코드 저장됨: {result2}")
    
    # 사용자 입력 받기
    print("\n" + "="*50)
    user_text = input("바코드로 변환할 텍스트를 입력하세요: ")
    if user_text:
        result = generate_barcode(user_text, "user_barcode")
        print(f"바코드가 저장되었습니다: {result}")
