"""
3단계: 인라인 데이터로 기능 테스트
테스트 코드 내에서 직접 데이터를 생성하여 각 모듈의 기능을 검증
"""

import pytest
import pandas as pd
from module.NFS_STRPROFILE import STRProfile
import module.NFS_PROFILEDATAMANAGER as NFS_PM
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.NFS_REPORTPHRASER as NFS_RP
from module.NFS_DATAFRAME import sort_by_serial_number


class TestSTRProfileInline:
    """STRProfile 클래스 단위 테스트 (인라인 데이터)"""

    def test_initialization_empty(self):
        """빈 프로필 생성"""
        profile = STRProfile()
        assert profile.id == ""
        assert profile.profile == {}

    def test_initialization_with_data(self):
        """데이터와 함께 프로필 생성"""
        profile = STRProfile(
            id="Sample001",
            profile={"D3S1358": {"15", "16"}, "vWA": {"14", "17"}}
        )
        assert profile.id == "Sample001"
        assert len(profile.profile) == 2
        assert profile.profile["D3S1358"] == {"15", "16"}

    def test_check_match_identical(self):
        """일치하는 프로필 비교"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"15", "16"}})

        assert profile1.check_match(profile2) is True

    def test_check_match_different(self):
        """일치하지 않는 프로필 비교"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"17", "18"}})

        assert profile1.check_match(profile2) is False

    def test_check_inclusion_true(self):
        """포함 관계 성립"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16", "17"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"15", "16"}})

        assert profile1.check_inclusion(profile2) is True

    def test_check_inclusion_false(self):
        """포함 관계 불성립"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"17", "18"}})

        assert profile1.check_inclusion(profile2) is False

    def test_union_profiles(self):
        """프로필 합집합"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"17"}})

        union = profile1.union_profiles(profile2)

        assert union.id == "A + B"
        assert union.profile["D3S1358"] == {"15", "16", "17"}

    def test_export_to_str_numeric(self):
        """숫자 대립유전자 정렬 테스트"""
        profile = STRProfile(
            id="Test",
            profile={"D3S1358": {"16", "15"}}
        )

        result = profile.export_to_str()

        # 숫자는 수치순 정렬
        assert result["D3S1358"] == "15-16"


class TestNFSProfileDataManagerInline:
    """NFSProfileDataManager 클래스 단위 테스트 (인라인 데이터)"""

    def test_initialization_default(self):
        """기본 초기화"""
        pm = NFS_PM.NFSProfileDataManager()

        assert pm.kit == "STR"
        assert isinstance(pm.df_profile, pd.DataFrame)
        assert pm.df_profile.empty

    def test_initialization_ystr(self):
        """YSTR 키트 초기화"""
        pm = NFS_PM.NFSProfileDataManager(kit="YSTR")

        assert pm.kit == "YSTR"

    def test_dict_markers_str(self):
        """STR 마커 확인"""
        pm = NFS_PM.NFSProfileDataManager(kit="STR")

        # DICT_MARKERS는 모듈 상수 직접 사용
        from module.constants_strprofile import DICT_MARKERS
        assert "STR" in DICT_MARKERS
        assert "AMEL" in DICT_MARKERS["STR"]
        assert "D3S1358" in DICT_MARKERS["STR"]
        assert len(DICT_MARKERS["STR"]) == 24

    def test_dict_markers_ystr(self):
        """YSTR 마커 확인"""
        pm = NFS_PM.NFSProfileDataManager(kit="YSTR")

        # DICT_MARKERS는 모듈 상수 직접 사용
        from module.constants_strprofile import DICT_MARKERS
        assert "YSTR" in DICT_MARKERS
        assert "DYS576" in DICT_MARKERS["YSTR"]
        assert len(DICT_MARKERS["YSTR"]) == 20

    # create_empty_strprofile 메서드는 실제로 존재하지 않으므로 테스트 제거


class TestNFSReportInformationInline:
    """NFSReportInformation 클래스 단위 테스트 (인라인 데이터)"""

    def test_initialization_default(self):
        """기본 초기화"""
        info = NFS_RI.NFSReportInformation()

        assert info.id_case == "noname"
        assert info.report_type == "default"
        assert info.caseinfo == {}
        assert info.evidenceinfo.empty

    def test_initialization_with_params(self):
        """파라미터와 함께 초기화"""
        info = NFS_RI.NFSReportInformation(id_case="2025-C-1234", report_type="test")

        assert info.id_case == "2025-C-1234"
        assert info.report_type == "test"

    def test_extract_caseinfo_from_df(self):
        """사건정보 추출 (인라인 DataFrame)"""
        # 테스트용 DataFrame 생성
        df = pd.DataFrame({
            '접수번호': ['2025-C-1234', '2025-C-5678'],
            '의뢰관서': ['서울지방경찰청', '부산지방경찰청'],
            '문서번호': ['DOC001', 'DOC002'],
            '접수일자': ['2025-01-01', '2025-01-02'],
            '시행일자': ['2025-01-10', '2025-01-11']
        })

        info = NFS_RI.NFSReportInformation(id_case='2025-C-1234')
        info.extract_caseinfo_from_df(df)

        assert info.caseinfo['의뢰관서'] == '서울지방경찰청'
        assert info.caseinfo['문서번호'] == 'DOC001'

    def test_extract_evidenceinfo_from_df(self):
        """증거물정보 추출 (인라인 DataFrame)"""
        df = pd.DataFrame({
            '접수번호': ['2025-C-1234', '2025-C-1234', '2025-C-5678'],
            '감정물번호': ['2025-C-1234-1', '2025-C-1234-2', '2025-C-5678-1'],
            '감정물': ['혈흔', '타액', '모발'],
            '분류': ['증거물', '증거물', '증거물'],
            '대조_이름': ['피의자A', '피의자B', '피해자C'],
            'Y_대조_이름': ['', '', ''],
            '프로필_유형': ['대조', '대조', '대조'],
            'Y_프로필_유형': ['', '', ''],
            '코드': ['V', 'V', 'V'],
            'Y_코드': ['', '', ''],
            '표기번호': ['증1호', '증2호', '증3호'],
            'Y_표기번호': ['', '', ''],
            '기재_여부': ['기재', '기재', '기재'],
            'Y_기재_여부': ['미기재', '미기재', '미기재'],
            '타액_반응': ['', '+', ''],
            '정액_반응': ['', '', ''],
            '혈흔_반응': ['+', '', ''],
            '검색_결과': ['', '', ''],
            '반환_여부': ['N', 'N', 'N']
        })

        info = NFS_RI.NFSReportInformation(id_case='2025-C-1234')
        info.extract_evidenceinfo_from_df(df)

        assert len(info.evidenceinfo) == 2  # 2개의 증거물
        assert '감정물번호' in info.evidenceinfo.columns


class TestNFSReportWriterInline:
    """NFSReportWriter 클래스 단위 테스트 (인라인 데이터)"""

    def test_initialization(self):
        """ReportWriter 초기화"""
        # 기본 evidenceinfo 구조를 가진 ReportInformation 생성
        info = NFS_RI.NFSReportInformation(id_case="test")
        info.evidenceinfo = pd.DataFrame({
            '접수번호': [],
            '감정물번호': [],
            '감정물': [],
            '분류': [],
            '대조_이름': [],
            'Y_대조_이름': [],
            '프로필_유형': [],
            'Y_프로필_유형': [],
            '코드': [],
            'Y_코드': [],
            '표기번호': [],
            'Y_표기번호': [],
            '기재_여부': [],
            'Y_기재_여부': [],
            '타액_반응': [],
            '정액_반응': [],
            '혈흔_반응': [],
            '검색_결과': [],
            '반환_여부': []
        })

        rw = NFS_RW.NFSReportWriter(info, [])

        assert rw.report_data.id_case == "test"
        assert rw.paths_picture == []
        assert rw.phrases_result == []

        # 블록 매니저가 생성되었는지 확인
        assert hasattr(rw, 'blocks_manager')
        assert "STR" in rw.blocks_manager
        assert "YSTR" in rw.blocks_manager

    def test_properties_phrase_dataclass(self):
        """Properties_Phrase 데이터클래스"""
        props = NFS_RP.Properties_Phrase(
            gender="남성",
            likelihoodratio=("1.5", "12"),
            text_evidence="증1호~증3호",
            nickname="피의자A"
        )

        assert props.gender == "남성"
        assert props.likelihoodratio == ("1.5", "12")
        assert props.text_evidence == "증1호~증3호"
        assert props.nickname == "피의자A"

    def test_block_profile_dataclass(self):
        """BlockProfile 데이터클래스"""
        block = NFS_RW.BlockProfile(
            idx_first="0",
            nickname="피의자A",
            text_table="증1호",
            id_ref="2025-C-1234-1",
            text_phrase=""
        )

        assert block.idx_first == "0"
        assert block.nickname == "피의자A"


class TestNFSReportPhraserInline:
    """NFS_REPORTPHRASER 함수들 단위 테스트 (인라인 데이터)"""

    def test_make_phrase_ref_normal(self, monkeypatch):
        """일반 대조 phrase (식별지수 포함)"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        props = NFS_RP.Properties_Phrase(
            gender="남성",
            likelihoodratio=("1.5", "12"),
            text_evidence="증1호~증3호",
            nickname="피의자A"
        )

        phrase = NFS_RP.make_phrase_ref(props)

        assert "디엔에이형이 검출되고" in phrase
        assert "일치함" in phrase
        assert "개인식별지수" in phrase
        assert "1.5 x 1012" in phrase

    def test_make_phrase_ref_victim_excluded(self, monkeypatch):
        """피해자 대조 phrase (식별지수 제외)"""
        monkeypatch.setattr('builtins.input', lambda x: 'y')

        props = NFS_RP.Properties_Phrase(
            gender="여성",
            likelihoodratio=("2.0", "15"),
            text_evidence="증4호",
            nickname="피해자 김철수"
        )

        phrase = NFS_RP.make_phrase_ref(props)

        assert "디엔에이형이 검출됨" in phrase
        assert "개인식별지수" not in phrase

    def test_make_phrase_res(self):
        """대표 phrase"""
        props = NFS_RP.Properties_Phrase(
            gender="",
            likelihoodratio=("", ""),
            text_evidence="증5호",
            nickname="대표1"
        )

        phrase = NFS_RP.make_phrase_res(props)

        assert "대표1의 디엔에이형이 검출됨" in phrase

    def test_make_phrase_nd(self):
        """ND phrase"""
        props = NFS_RP.Properties_Phrase(
            gender="",
            likelihoodratio=("", ""),
            text_evidence="증6호~증8호",
            nickname=""
        )

        phrase = NFS_RP.make_phrase_nd(props)

        assert "증6호~증8호에서 디엔에이형이 검출되지 않음" in phrase

    def test_make_phrase_nc(self):
        """NC phrase"""
        props = NFS_RP.Properties_Phrase(
            gender="",
            likelihoodratio=("", ""),
            text_evidence="증9호",
            nickname=""
        )

        phrase = NFS_RP.make_phrase_nc(props)

        assert "증9호에서 디엔에이형을 특정할 수 없음" in phrase


class TestDataFrameUtilsInline:
    """DataFrame 유틸리티 함수들 단위 테스트 (인라인 데이터)"""

    def test_sort_by_serial_number(self):
        """일련번호 자연 정렬"""
        df = pd.DataFrame({
            '코드': ['2025-C-1234-10', '2025-C-1234-2', '2025-C-1234-1']
        })

        sorted_df = sort_by_serial_number(df, '코드')

        # 정렬 확인: 1, 2, 10 순서
        codes = list(sorted_df['코드'])
        assert codes[0] == '2025-C-1234-1'
        assert codes[1] == '2025-C-1234-2'
        assert codes[2] == '2025-C-1234-10'


class TestEdgeCasesInline:
    """엣지 케이스 테스트 (인라인 데이터)"""

    def test_empty_dataframe_extract_evidenceinfo(self):
        """빈 DataFrame으로 증거물 추출"""
        from module.exceptions import CaseNotFoundError

        df = pd.DataFrame()
        info = NFS_RI.NFSReportInformation(id_case='2025-C-1234')

        # 리팩토링 후: CaseNotFoundError 발생
        with pytest.raises(CaseNotFoundError):
            info.extract_evidenceinfo_from_df(df)

    def test_case_not_found_extract_caseinfo(self):
        """존재하지 않는 사건번호로 추출"""
        from module.exceptions import CaseNotFoundError

        df = pd.DataFrame({
            '접수번호': ['2025-C-5678'],
            '의뢰관서': ['서울지방경찰청'],
            '문서번호': ['DOC001'],
            '접수일자': ['2025-01-01'],
            '시행일자': ['2025-01-10']
        })

        info = NFS_RI.NFSReportInformation(id_case='2025-C-9999')  # 존재하지 않음

        # CaseNotFoundError 발생할 것으로 예상
        with pytest.raises(CaseNotFoundError):
            info.extract_caseinfo_from_df(df)

    def test_strprofile_with_none(self):
        """None으로 STRProfile 생성"""
        profile = STRProfile(id=None, profile=None)

        # 실제 동작: None을 그대로 저장
        assert profile.id is None
        assert profile.profile == {}  # profile은 {}로 처리됨
