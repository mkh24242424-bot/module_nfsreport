"""
pytest 설정 및 공통 fixture
테스트 실패 시 예상값과 실제값을 명확하게 출력
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ==================== Test Data Fixtures ====================

@pytest.fixture(scope="session")
def testdata_dir():
    """testdata 디렉토리 경로"""
    return project_root / "testdata"


@pytest.fixture(scope="session")
def df_caseinfo(testdata_dir):
    """사건정보 데이터프레임 (세션당 1회 로드)"""
    return pd.read_csv(testdata_dir / "test_df_caseinfo.csv")


@pytest.fixture(scope="session")
def df_report(testdata_dir):
    """증거물 리포트 데이터프레임 (세션당 1회 로드)"""
    return pd.read_csv(testdata_dir / "test_df_report.csv")


@pytest.fixture(scope="session")
def df_profile_str(testdata_dir):
    """STR 프로필 데이터프레임 (세션당 1회 로드)"""
    return pd.read_csv(testdata_dir / "test_df_profile_str.csv")


@pytest.fixture(scope="session")
def df_profile_ystr(testdata_dir):
    """Y-STR 프로필 데이터프레임 (세션당 1회 로드)"""
    return pd.read_csv(testdata_dir / "test_df_profile_ystr.csv")


@pytest.fixture
def sample_case_id():
    """테스트용 샘플 사건번호 (main.py에서 사용하는 것과 동일)"""
    return "2025-C-6845"


# ==================== Custom Assertion Helpers ====================

def format_comparison(expected, actual, description=""):
    """예상값과 실제값을 보기 좋게 포맷팅"""
    separator = "=" * 80
    output = [
        "",
        separator,
        f"테스트 실패: {description}" if description else "테스트 실패",
        separator,
        "",
        "【예상값 (Expected)】",
        str(expected),
        "",
        "【실제값 (Actual)】",
        str(actual),
        "",
    ]

    # 타입이 다른 경우
    if type(expected) != type(actual):
        output.extend([
            "【타입 차이】",
            f"예상 타입: {type(expected).__name__}",
            f"실제 타입: {type(actual).__name__}",
            ""
        ])

    # DataFrame인 경우 추가 정보
    if isinstance(expected, pd.DataFrame) or isinstance(actual, pd.DataFrame):
        output.extend([
            "【DataFrame 비교】",
            f"예상 shape: {expected.shape if isinstance(expected, pd.DataFrame) else 'N/A'}",
            f"실제 shape: {actual.shape if isinstance(actual, pd.DataFrame) else 'N/A'}",
        ])

        if isinstance(expected, pd.DataFrame) and isinstance(actual, pd.DataFrame):
            # 컬럼 비교
            exp_cols = set(expected.columns)
            act_cols = set(actual.columns)
            if exp_cols != act_cols:
                output.extend([
                    "",
                    "【컬럼 차이】",
                    f"예상에만 있는 컬럼: {exp_cols - act_cols}",
                    f"실제에만 있는 컬럼: {act_cols - exp_cols}",
                ])
        output.append("")

    # 리스트나 세트인 경우 추가 정보
    if isinstance(expected, (list, set)) and isinstance(actual, (list, set)):
        output.extend([
            "【길이 비교】",
            f"예상 길이: {len(expected)}",
            f"실제 길이: {len(actual)}",
            ""
        ])

        if isinstance(expected, set) and isinstance(actual, set):
            output.extend([
                "【집합 차이】",
                f"예상에만 있음: {expected - actual}",
                f"실제에만 있음: {actual - expected}",
                ""
            ])

    output.append(separator)
    return "\n".join(output)


@pytest.fixture
def assert_equal_with_detail():
    """상세한 비교 출력을 제공하는 assertion 헬퍼"""
    def _assert(expected, actual, description=""):
        if expected != actual:
            msg = format_comparison(expected, actual, description)
            pytest.fail(msg)
    return _assert


@pytest.fixture
def assert_dataframe_equal():
    """DataFrame 비교를 위한 assertion 헬퍼"""
    def _assert(expected, actual, description=""):
        try:
            pd.testing.assert_frame_equal(expected, actual)
        except AssertionError as e:
            msg = format_comparison(expected, actual, description)
            msg += f"\n\nPandas 상세 에러:\n{str(e)}"
            pytest.fail(msg)
    return _assert


# ==================== Pytest Hooks ====================

def pytest_assertrepr_compare(op, left, right):
    """pytest의 기본 assertion 출력을 개선"""
    if op == "==":
        # DataFrame 비교
        if isinstance(left, pd.DataFrame) and isinstance(right, pd.DataFrame):
            return [
                "DataFrame 비교 실패:",
                f"Left shape: {left.shape}, Right shape: {right.shape}",
                f"Left columns: {list(left.columns)}",
                f"Right columns: {list(right.columns)}",
            ]

        # 리스트 비교 (길이가 긴 경우)
        if isinstance(left, list) and isinstance(right, list):
            if len(left) > 10 or len(right) > 10:
                return [
                    "List 비교 실패:",
                    f"Left length: {len(left)}, Right length: {len(right)}",
                    f"First difference at index: {next((i for i, (l, r) in enumerate(zip(left, right)) if l != r), None)}",
                ]


# ==================== 테스트 실행 전후 로깅 ====================

@pytest.fixture(autouse=True)
def test_logger(request):
    """각 테스트 실행 전후에 로그 출력"""
    test_name = request.node.name
    print(f"\n▶ 테스트 시작: {test_name}")
    yield
    print(f"✓ 테스트 완료: {test_name}")
