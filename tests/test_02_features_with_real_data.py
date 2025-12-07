"""
2단계: 주어진 데이터로 각 기능 테스트
testdata/ CSV 파일을 사용하여 각 모듈의 기능을 개별적으로 검증
"""

import pytest
import pandas as pd

import module.NFS_PROFILEDATAMANAGER as NFS_PM
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.NFS_REPORTPHRASER as NFS_RP
from module.NFS_STRPROFILE import STRProfile


class TestNFSReportInformationWithRealData:
    """NFSReportInformation 클래스 기능 테스트 (실제 데이터)"""

    def test_extract_caseinfo_from_df(self, df_caseinfo, sample_case_id):
        """사건정보 추출 테스트"""
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)

        # 검증
        assert info.caseinfo is not None
        assert isinstance(info.caseinfo, dict)

        # 필수 키 확인
        required_keys = ['의뢰관서', '문서번호', '접수일자', '시행일자']
        for key in required_keys:
            assert key in info.caseinfo, f"필수 키 '{key}'가 없습니다"
            assert info.caseinfo[key] is not None, f"'{key}' 값이 None입니다"

        print(f"\n✓ 사건정보 추출 성공:")
        print(f"  - 의뢰관서: {info.caseinfo['의뢰관서']}")
        print(f"  - 접수일자: {info.caseinfo['접수일자']}")

    def test_extract_evidenceinfo_from_df(self, df_report, sample_case_id):
        """증거물정보 추출 테스트"""
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_evidenceinfo_from_df(df_report)

        # 검증
        assert not info.evidenceinfo.empty, "evidenceinfo가 비어있습니다"
        assert isinstance(info.evidenceinfo, pd.DataFrame)

        # 필수 컬럼 확인
        required_cols = ['감정물번호', '감정물', '분류', '대조_이름', 'Y_대조_이름',
                         '프로필_유형', 'Y_프로필_유형', '코드', 'Y_코드']
        for col in required_cols:
            assert col in info.evidenceinfo.columns, f"필수 컬럼 '{col}'이 없습니다"

        print(f"\n✓ 증거물정보 추출 성공:")
        print(f"  - 증거물 수: {len(info.evidenceinfo)}")
        print(f"  - 컬럼 수: {len(info.evidenceinfo.columns)}")

    def test_load_str_profiledatamanager(self, df_caseinfo, df_report,
                                          df_profile_str, sample_case_id):
        """STR ProfileDataManager 로딩 테스트"""
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str

        info.load_str_profiledatamanager(pm_str)

        # 검증
        assert info.pm_str is not None, "pm_str이 로드되지 않았습니다"
        assert isinstance(info.pm_str, NFS_PM.NFSProfileDataManager)
        assert info.pm_str.kit == "STR"

        print(f"\n✓ STR ProfileDataManager 로딩 성공:")
        print(f"  - 프로필 수: {len(info.pm_str.df_profile)}")

    def test_load_ystr_profiledatamanager(self, df_caseinfo, df_report,
                                           df_profile_ystr, sample_case_id):
        """YSTR ProfileDataManager 로딩 테스트"""
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr

        info.load_ystr_profiledatamanager(pm_ystr)

        # 검증
        assert info.pm_ystr is not None, "pm_ystr이 로드되지 않았습니다"
        assert isinstance(info.pm_ystr, NFS_PM.NFSProfileDataManager)
        assert info.pm_ystr.kit == "YSTR"

        print(f"\n✓ YSTR ProfileDataManager 로딩 성공:")
        print(f"  - 프로필 수: {len(info.pm_ystr.df_profile)}")


class TestNFSProfileDataManagerWithRealData:
    """NFSProfileDataManager 클래스 기능 테스트 (실제 데이터)"""

    def test_initialization_str(self, df_profile_str):
        """STR ProfileDataManager 초기화 테스트"""
        pm = NFS_PM.NFSProfileDataManager(kit="STR")
        pm.df_profile = df_profile_str

        assert pm.kit == "STR"
        assert not pm.df_profile.empty
        assert len(pm.df_profile) == len(df_profile_str)

        # DICT_MARKERS 확인 (모듈 상수 직접 사용)
        from module.constants_strprofile import DICT_MARKERS
        assert "STR" in DICT_MARKERS
        assert len(DICT_MARKERS["STR"]) == 24  # STR 마커 24개

        print(f"\n✓ STR ProfileDataManager 초기화 성공:")
        print(f"  - 마커 수: {len(DICT_MARKERS['STR'])}")

    def test_initialization_ystr(self, df_profile_ystr):
        """YSTR ProfileDataManager 초기화 테스트"""
        pm = NFS_PM.NFSProfileDataManager(kit="YSTR")
        pm.df_profile = df_profile_ystr

        assert pm.kit == "YSTR"
        assert not pm.df_profile.empty
        assert len(pm.df_profile) == len(df_profile_ystr)

        # DICT_MARKERS 확인 (모듈 상수 직접 사용)
        from module.constants_strprofile import DICT_MARKERS
        assert "YSTR" in DICT_MARKERS
        assert len(DICT_MARKERS["YSTR"]) == 20  # YSTR 마커 20개

        print(f"\n✓ YSTR ProfileDataManager 초기화 성공:")
        print(f"  - 마커 수: {len(DICT_MARKERS['YSTR'])}")

    def test_filter_by_codecase(self, df_profile_str, sample_case_id):
        """사건번호로 프로필 필터링 테스트"""
        pm = NFS_PM.NFSProfileDataManager(kit="STR")
        pm.df_profile = df_profile_str

        # 필터링
        filtered_pm = pm.filter_by_codecase(code_case=sample_case_id)

        # 검증
        if filtered_pm is not None:
            assert isinstance(filtered_pm, NFS_PM.NFSProfileDataManager)
            assert filtered_pm.kit == "STR"

            # 필터링된 데이터가 해당 사건번호만 포함하는지 확인
            if not filtered_pm.df_profile.empty:
                assert all(filtered_pm.df_profile['접수번호'] == sample_case_id)

            print(f"\n✓ 사건번호로 필터링 성공:")
            print(f"  - 필터링된 프로필 수: {len(filtered_pm.df_profile)}")
        else:
            print(f"\n✓ 해당 사건번호의 프로필 없음 (None 반환)")


class TestNFSReportWriterWithRealData:
    """NFSReportWriter 클래스 기능 테스트 (실제 데이터)"""

    def test_block_manager_creation(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      sample_case_id):
        """블록 매니저 자동 생성 테스트 (새 구조)"""
        # 데이터 준비
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr
        info.load_ystr_profiledatamanager(pm_ystr)

        RW = NFS_RW.NFSReportWriter(info, [])

        # 블록 매니저 검증
        assert hasattr(RW, 'blocks_manager')
        assert "STR" in RW.blocks_manager
        assert "YSTR" in RW.blocks_manager

        str_blocks = RW.blocks_manager["STR"].blocks
        assert isinstance(str_blocks, dict)

        print(f"\n✓ 블록 매니저 생성 성공:")
        print(f"  - 블록 유형: {list(str_blocks.keys())}")

        for block_type, blocks in str_blocks.items():
            print(f"  - {block_type}: {len(blocks)}개")

    def test_evidence_text_generator(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      sample_case_id):
        """EvidenceTextGenerator 메서드 테스트 (새 구조)"""
        # 데이터 준비
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr
        info.load_ystr_profiledatamanager(pm_ystr)

        RW = NFS_RW.NFSReportWriter(info, [])

        # evidence_text_generator 접근
        text_gen = RW.blocks_manager["STR"].evidence_text_generator

        # 샘플 ID로 텍스트 생성 테스트
        sample_ids = info.evidenceinfo['감정물번호'].head(3).tolist()
        if sample_ids:
            text_evidence = text_gen.create_text_evidence(
                list_id=sample_ids,
                kit="STR"
            )

            # 검증
            assert text_evidence is not None
            assert isinstance(text_evidence, str)

            print(f"\n✓ evidence_text_generator 성공:")
            print(f"  - ID 수: {len(sample_ids)}")
            print(f"  - 생성된 텍스트: {text_evidence}")


class TestNFSReportPhraserWithRealData:
    """NFS_REPORTPHRASER 함수들 테스트 (실제 데이터)"""

    def test_make_phrase_ref(self, df_caseinfo, df_report,
                              df_profile_str, df_profile_ystr,
                              sample_case_id, monkeypatch):
        """make_phrase_ref 함수 테스트"""
        # 사용자 입력 mock
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        # 데이터 준비
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        RW = NFS_RW.NFSReportWriter(info, [])

        # Properties_Phrase 생성 (NFS_RP에서 가져옴)
        properties = NFS_RP.Properties_Phrase(
            gender="남성",
            likelihoodratio=("1.23", "10"),
            text_evidence="증1호~증3호",
            nickname="피의자A"
        )

        # Phrase 생성
        phrase = NFS_RP.make_phrase_ref(properties)

        # 검증
        assert phrase is not None
        assert isinstance(phrase, str)
        assert len(phrase) > 0
        assert "디엔에이형" in phrase
        assert "일치" in phrase

        print(f"\n✓ make_phrase_ref 성공:")
        print(f"  - 생성된 phrase: {phrase}")

    def test_make_phrase_res(self):
        """make_phrase_res 함수 테스트"""
        properties = NFS_RP.Properties_Phrase(
            gender="여성",
            likelihoodratio=("", ""),
            text_evidence="증4호",
            nickname="대표1"
        )

        phrase = NFS_RP.make_phrase_res(properties)

        assert phrase is not None
        assert isinstance(phrase, str)
        assert "디엔에이형이 검출됨" in phrase

        print(f"\n✓ make_phrase_res 성공:")
        print(f"  - 생성된 phrase: {phrase}")

    def test_make_phrase_nd(self):
        """make_phrase_nd 함수 테스트"""
        properties = NFS_RP.Properties_Phrase(
            gender="",
            likelihoodratio=("", ""),
            text_evidence="증5호~증7호",
            nickname=""
        )

        phrase = NFS_RP.make_phrase_nd(properties)

        assert phrase is not None
        assert isinstance(phrase, str)
        assert "디엔에이형이 검출되지 않음" in phrase

        print(f"\n✓ make_phrase_nd 성공:")
        print(f"  - 생성된 phrase: {phrase}")

    def test_make_phrase_nc(self):
        """make_phrase_nc 함수 테스트"""
        properties = NFS_RP.Properties_Phrase(
            gender="",
            likelihoodratio=("", ""),
            text_evidence="증8호",
            nickname=""
        )

        phrase = NFS_RP.make_phrase_nc(properties)

        assert phrase is not None
        assert isinstance(phrase, str)
        assert "디엔에이형을 특정할 수 없음" in phrase

        print(f"\n✓ make_phrase_nc 성공:")
        print(f"  - 생성된 phrase: {phrase}")


class TestDataValidation:
    """실제 데이터의 유효성 검증"""

    def test_caseinfo_required_columns(self, df_caseinfo):
        """사건정보 필수 컬럼 확인"""
        required_cols = ['접수번호', '의뢰관서', '문서번호', '접수일자', '시행일자']

        for col in required_cols:
            assert col in df_caseinfo.columns, f"필수 컬럼 '{col}'이 없습니다"

        print(f"\n✓ 사건정보 필수 컬럼 확인 완료: {required_cols}")

    def test_report_required_columns(self, df_report):
        """증거물 리포트 필수 컬럼 확인"""
        required_cols = ['접수번호', '감정물번호', '감정물', '프로필_유형',
                         '코드', '표기번호', '기재_여부']

        for col in required_cols:
            assert col in df_report.columns, f"필수 컬럼 '{col}'이 없습니다"

        print(f"\n✓ 증거물 리포트 필수 컬럼 확인 완료")

    def test_profile_str_required_columns(self, df_profile_str):
        """STR 프로필 필수 컬럼 확인"""
        required_cols = ['접수번호', '감정물번호', 'AMEL', 'D3S1358', 'vWA']

        for col in required_cols:
            assert col in df_profile_str.columns, f"필수 컬럼 '{col}'이 없습니다"

        print(f"\n✓ STR 프로필 필수 컬럼 확인 완료")

    def test_case_id_exists(self, df_caseinfo, sample_case_id):
        """샘플 사건번호가 데이터에 존재하는지 확인"""
        assert sample_case_id in df_caseinfo['접수번호'].values, \
            f"사건번호 '{sample_case_id}'가 데이터에 없습니다"

        print(f"\n✓ 샘플 사건번호 존재 확인: {sample_case_id}")
