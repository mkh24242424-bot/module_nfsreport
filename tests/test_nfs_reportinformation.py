"""
NFS_REPORTINFORMATION 모듈 테스트
NFSReportInformation 클래스의 기능을 검증합니다.
"""

import pytest
import pandas as pd
from module.NFS_REPORTINFORMATION import NFSReportInformation
from module.NFS_PROFILEDATAMANAGER import NFSProfileDataManager


class TestNFSReportInformationInit:
    """NFSReportInformation 초기화 테스트"""

    def test_default_initialization(self):
        """기본 초기화"""
        report_info = NFSReportInformation()
        assert report_info.id_case == "noname"
        assert report_info.type_case == "default"
        assert report_info.caseinfo == {}
        assert isinstance(report_info.evidenceinfo, pd.DataFrame)
        assert report_info.evidenceinfo.empty
        assert report_info.pm_str is None
        assert report_info.pm_ystr is None

    def test_initialization_with_parameters(self):
        """파라미터로 초기화"""
        report_info = NFSReportInformation(id_case="2023-D-1234", type_case="친자")
        assert report_info.id_case == "2023-D-1234"
        assert report_info.type_case == "친자"
        assert report_info.caseinfo == {}
        assert report_info.pm_str is None
        assert report_info.pm_ystr is None


class TestExtractCaseinfoFromDf:
    """extract_caseinfo_from_df() 메서드 테스트"""

    def test_extract_existing_case(self):
        """존재하는 사건번호로 정보 추출"""
        report_info = NFSReportInformation(id_case="2023-D-1234")
        df_caseinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1235'],
            '의뢰관서': ['서울지방경찰청', '부산지방경찰청'],
            '문서번호': ['서경형 123456', '부경형 654321'],
            '접수일자': ['2023-01-15', '2023-01-16'],
            '시행일자': ['2023-02-15', '2023-02-16'],
            '기타정보': ['extra1', 'extra2']
        })

        report_info.extract_caseinfo_from_df(df_caseinfo)

        assert report_info.caseinfo['의뢰관서'] == '서울지방경찰청'
        assert report_info.caseinfo['문서번호'] == '서경형 123456'
        assert report_info.caseinfo['접수일자'] == '2023-01-15'
        assert report_info.caseinfo['시행일자'] == '2023-02-15'
        assert '기타정보' not in report_info.caseinfo  # 필수 컬럼에 없음

    def test_extract_nonexistent_case(self):
        """존재하지 않는 사건번호 (빈 결과, 에러 메시지 출력)"""
        report_info = NFSReportInformation(id_case="9999-D-9999")
        df_caseinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '의뢰관서': ['서울지방경찰청'],
            '문서번호': ['서경형 123456'],
            '접수일자': ['2023-01-15'],
            '시행일자': ['2023-02-15']
        })

        # IndexError 발생 가능 - iloc[0]에서 빈 결과
        with pytest.raises(IndexError):
            report_info.extract_caseinfo_from_df(df_caseinfo)

    def test_extract_missing_column(self, capsys):
        """필수 컬럼이 누락된 경우 KeyError 처리"""
        report_info = NFSReportInformation(id_case="2023-D-1234")
        df_caseinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '의뢰관서': ['서울지방경찰청'],
            # '문서번호' 누락
            '접수일자': ['2023-01-15'],
            '시행일자': ['2023-02-15']
        })

        report_info.extract_caseinfo_from_df(df_caseinfo)
        captured = capsys.readouterr()
        assert '문서번호' in captured.out or '사건 정보가 데이터프레임에 존재하지 않습니다' in captured.out


class TestExtractEvidenceinfoFromDf:
    """extract_evidenceinfo_from_df() 메서드 테스트"""

    def test_extract_existing_evidence(self):
        """존재하는 사건번호로 증거물 정보 추출"""
        report_info = NFSReportInformation(id_case="2023-D-1234")
        df_evidenceinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1234', '2023-D-1235'],
            '감정물번호': ['2023-D-1234-1', '2023-D-1234-2', '2023-D-1235-1'],
            '감정물': ['혈흔', '타액', '모근'],
            '분류': ['증거물', '증거물', '증거물'],
            '대조_이름': ['피의자A', '', '피의자B'],
            'Y_대조_이름': ['', '', ''],
            '프로필_유형': ['일반', '일반', '일반'],
            'Y_프로필_유형': ['', '', ''],
            '코드': ['2023-D-1234-1', '2023-D-1234-2', '2023-D-1235-1'],
            'Y_코드': ['', '', ''],
            '표기번호': ['증1호', '증2호', '증1호'],
            'Y_표기번호': ['', '', ''],
            '기재_여부': ['기재', '기재', '기재'],
            'Y_기재_여부': ['미기재', '미기재', '미기재'],
            '타액_반응': ['실험 안함', '양성', '실험 안함'],
            '정액_반응': ['실험 안함', '실험 안함', '실험 안함'],
            '혈흔_반응': ['양성', '실험 안함', '실험 안함'],
            '검색_결과': ['', '', ''],
            '반환_여부': ['반환', '반환', '반환'],
            '기타정보': ['extra1', 'extra2', 'extra3']
        }, index=[0, 1, 5])  # 인덱스를 명시적으로 설정

        report_info.extract_evidenceinfo_from_df(df_evidenceinfo)

        assert len(report_info.evidenceinfo) == 2
        assert list(report_info.evidenceinfo['감정물번호']) == ['2023-D-1234-1', '2023-D-1234-2']
        # 인덱스는 원본 유지
        assert list(report_info.evidenceinfo.index) == [0, 1]
        # 필수 컬럼만 포함
        assert '기타정보' not in report_info.evidenceinfo.columns

    def test_extract_nonexistent_evidence(self):
        """존재하지 않는 사건번호로 증거물 정보 추출 (빈 DataFrame)"""
        report_info = NFSReportInformation(id_case="9999-D-9999")
        df_evidenceinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            '감정물': ['혈흔'],
            '분류': ['증거물'],
            '대조_이름': ['피의자A'],
            'Y_대조_이름': [''],
            '프로필_유형': ['일반'],
            'Y_프로필_유형': [''],
            '코드': ['2023-D-1234-1'],
            'Y_코드': [''],
            '표기번호': ['증1호'],
            'Y_표기번호': [''],
            '기재_여부': ['기재'],
            'Y_기재_여부': ['미기재'],
            '타액_반응': ['실험 안함'],
            '정액_반응': ['실험 안함'],
            '혈흔_반응': ['양성'],
            '검색_결과': [''],
            '반환_여부': ['반환']
        })

        report_info.extract_evidenceinfo_from_df(df_evidenceinfo)
        assert len(report_info.evidenceinfo) == 0

    def test_extract_missing_column(self, capsys):
        """필수 컬럼이 누락된 경우 KeyError 처리"""
        report_info = NFSReportInformation(id_case="2023-D-1234")
        df_evidenceinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            # '감정물' 누락
            '분류': ['증거물']
        })

        report_info.extract_evidenceinfo_from_df(df_evidenceinfo)
        captured = capsys.readouterr()
        assert '감정물' in captured.out or '사건 정보가 데이터프레임에 존재하지 않습니다' in captured.out

    def test_index_preservation(self):
        """DataFrame 인덱스 보존 확인"""
        report_info = NFSReportInformation(id_case="2023-D-1234")
        df_evidenceinfo = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1234', '2023-D-1234'],
            '감정물번호': ['2023-D-1234-1', '2023-D-1234-2', '2023-D-1234-3'],
            '감정물': ['혈흔', '타액', '모근'],
            '분류': ['증거물', '증거물', '증거물'],
            '대조_이름': ['', '', ''],
            'Y_대조_이름': ['', '', ''],
            '프로필_유형': ['일반', '일반', '일반'],
            'Y_프로필_유형': ['', '', ''],
            '코드': ['2023-D-1234-1', '2023-D-1234-2', '2023-D-1234-3'],
            'Y_코드': ['', '', ''],
            '표기번호': ['증1호', '증2호', '증3호'],
            'Y_표기번호': ['', '', ''],
            '기재_여부': ['기재', '기재', '기재'],
            'Y_기재_여부': ['미기재', '미기재', '미기재'],
            '타액_반응': ['실험 안함', '실험 안함', '실험 안함'],
            '정액_반응': ['실험 안함', '실험 안함', '실험 안함'],
            '혈흔_반응': ['실험 안함', '실험 안함', '실험 안함'],
            '검색_결과': ['', '', ''],
            '반환_여부': ['반환', '반환', '반환']
        }, index=[5, 8, 12])  # 비연속 인덱스

        report_info.extract_evidenceinfo_from_df(df_evidenceinfo)
        # 원본 인덱스 [5, 8, 12]가 유지되어야 함
        assert list(report_info.evidenceinfo.index) == [5, 8, 12]


class TestLoadProfileDataManager:
    """ProfileDataManager 로드 메서드 테스트"""

    def test_load_str_profiledatamanager(self):
        """STR ProfileDataManager 로드"""
        report_info = NFSReportInformation(id_case="2023-D-1234")

        # Mock ProfileDataManager
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1235'],
            '감정물번호': ['2023-D-1234-1', '2023-D-1235-1'],
            'AMEL': ['XY', 'XX']
        })

        report_info.load_str_profiledatamanager(pdm)

        assert report_info.pm_str is not None
        assert isinstance(report_info.pm_str, NFSProfileDataManager)
        # 필터링되어 해당 사건번호만 포함
        assert len(report_info.pm_str.df_profile) == 1

    def test_load_ystr_profiledatamanager(self):
        """Y-STR ProfileDataManager 로드"""
        report_info = NFSReportInformation(id_case="2023-D-1234")

        # Mock ProfileDataManager
        pdm = NFSProfileDataManager(kit="YSTR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1235'],
            '감정물번호': ['2023-D-1234-1', '2023-D-1235-1'],
            'DYS576': ['15', '16']
        })

        report_info.load_ystr_profiledatamanager(pdm)

        assert report_info.pm_ystr is not None
        assert isinstance(report_info.pm_ystr, NFSProfileDataManager)
        # 필터링되어 해당 사건번호만 포함
        assert len(report_info.pm_ystr.df_profile) == 1
