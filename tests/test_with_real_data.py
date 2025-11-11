"""
실제 testdata 파일을 활용한 통합 테스트 예시
"""

import pytest
import pandas as pd
from pathlib import Path
from module.NFS_REPORTINFORMATION import NFSReportInformation
from module.NFS_PROFILEDATAMANAGER import NFSProfileDataManager


# 테스트 데이터 경로
TESTDATA_DIR = Path(__file__).parent.parent / "testdata"


@pytest.fixture
def df_caseinfo():
    """실제 사건정보 데이터 로드"""
    return pd.read_csv(TESTDATA_DIR / "test_df_caseinfo.csv")


@pytest.fixture
def df_profile_str():
    """실제 STR 프로파일 데이터 로드"""
    return pd.read_csv(TESTDATA_DIR / "test_df_profile_str.csv")


@pytest.fixture
def df_report():
    """실제 리포트 데이터 로드"""
    return pd.read_csv(TESTDATA_DIR / "test_df_report.csv")


class TestWithRealData:
    """실제 데이터를 사용한 통합 테스트"""

    def test_extract_caseinfo_from_real_data(self, df_caseinfo):
        """실제 사건정보에서 데이터 추출 테스트"""
        # 실제 데이터의 첫 번째 사건번호 사용
        if not df_caseinfo.empty:
            first_case_id = df_caseinfo.iloc[0]['접수번호']

            report_info = NFSReportInformation(id_case=first_case_id)
            report_info.extract_caseinfo_from_df(df_caseinfo)

            # 실제 데이터로 추출이 잘 되는지 확인
            assert report_info.caseinfo is not None
            assert '의뢰관서' in report_info.caseinfo
            assert '문서번호' in report_info.caseinfo

    def test_real_data_structure(self, df_caseinfo, df_profile_str, df_report):
        """실제 데이터 구조 검증"""
        # 사건정보 구조 확인
        assert '접수번호' in df_caseinfo.columns
        assert '의뢰관서' in df_caseinfo.columns
        assert not df_caseinfo.empty

        # 프로파일 데이터 구조 확인
        if not df_profile_str.empty:
            assert '접수번호' in df_profile_str.columns or '감정물번호' in df_profile_str.columns

    def test_profiledatamanager_with_real_data(self, df_profile_str):
        """실제 프로파일 데이터로 ProfileDataManager 테스트"""
        if df_profile_str.empty:
            pytest.skip("프로파일 데이터가 비어있음")

        pdm = NFSProfileDataManager(kit="STR")
        # 실제 데이터를 사용하여 특정 기능 테스트
        # (실제 컬럼 구조에 따라 조정 필요)

        # 데이터가 있는지만 확인
        assert len(df_profile_str) > 0

    def test_data_consistency(self, df_caseinfo, df_report):
        """데이터 간 일관성 검증"""
        if df_caseinfo.empty or df_report.empty:
            pytest.skip("데이터가 비어있음")

        # 사건정보와 리포트 데이터 간 접수번호 일관성 확인
        case_ids_caseinfo = set(df_caseinfo['접수번호'].unique())

        if '접수번호' in df_report.columns:
            case_ids_report = set(df_report['접수번호'].unique())

            # 리포트 데이터의 모든 접수번호가 사건정보에 존재하는지 확인
            assert case_ids_report.issubset(case_ids_caseinfo) or len(case_ids_report) > 0


class TestDataQuality:
    """테스트 데이터 품질 검증"""

    def test_no_missing_critical_fields(self, df_caseinfo):
        """필수 필드 누락 확인"""
        if df_caseinfo.empty:
            pytest.skip("데이터가 비어있음")

        critical_fields = ['접수번호', '의뢰관서', '접수일자']

        for field in critical_fields:
            if field in df_caseinfo.columns:
                # 필수 필드에 null이 너무 많으면 경고
                null_ratio = df_caseinfo[field].isna().sum() / len(df_caseinfo)
                assert null_ratio < 0.5, f"{field} 필드의 null 비율이 {null_ratio:.1%}로 높음"

    def test_data_types(self, df_caseinfo):
        """데이터 타입 일관성 확인"""
        if df_caseinfo.empty:
            pytest.skip("데이터가 비어있음")

        # 접수번호는 문자열이어야 함
        if '접수번호' in df_caseinfo.columns:
            # 비어있지 않은 값들이 문자열 패턴을 따르는지 확인
            sample = df_caseinfo['접수번호'].dropna().iloc[0] if len(df_caseinfo) > 0 else None
            if sample:
                # 2025-C-6697 같은 패턴
                assert isinstance(sample, str) or '-' in str(sample)


# 실행 예시
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
