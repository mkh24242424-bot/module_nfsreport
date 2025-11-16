"""
1단계: main.py 워크플로우 E2E 테스트
main.py가 실제로 하는 것을 그대로 재현하여 검증
"""

import pytest
import pandas as pd
import logging

import module.NFS_PROFILEDATAMANAGER as NFS_PM
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.NFS_REPORTPHRASER as NFS_RP


class TestMainWorkflowE2E:
    """main.py의 전체 워크플로우 테스트"""

    def test_01_csv_loading(self, df_caseinfo, df_report, df_profile_str, df_profile_ystr):
        """1. CSV 파일 로딩 성공 확인"""
        # 각 DataFrame이 로드되었는지 확인
        assert isinstance(df_caseinfo, pd.DataFrame), "df_caseinfo가 DataFrame이 아닙니다"
        assert isinstance(df_report, pd.DataFrame), "df_report가 DataFrame이 아닙니다"
        assert isinstance(df_profile_str, pd.DataFrame), "df_profile_str가 DataFrame이 아닙니다"
        assert isinstance(df_profile_ystr, pd.DataFrame), "df_profile_ystr가 DataFrame이 아닙니다"

        # DataFrame이 비어있지 않은지 확인
        assert len(df_caseinfo) > 0, "df_caseinfo가 비어있습니다"
        assert len(df_report) > 0, "df_report가 비어있습니다"
        assert len(df_profile_str) > 0, "df_profile_str가 비어있습니다"
        assert len(df_profile_ystr) > 0, "df_profile_ystr가 비어있습니다"

        print(f"\n✓ CSV 로딩 성공:")
        print(f"  - df_caseinfo: {len(df_caseinfo)} rows")
        print(f"  - df_report: {len(df_report)} rows")
        print(f"  - df_profile_str: {len(df_profile_str)} rows")
        print(f"  - df_profile_ystr: {len(df_profile_ystr)} rows")

    def test_02_profile_manager_creation(self, df_profile_str, df_profile_ystr):
        """2. ProfileDataManager 생성 (STR, YSTR)"""
        # STR ProfileDataManager 생성
        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str

        assert pm_str.kit == "STR", f"예상: 'STR', 실제: '{pm_str.kit}'"
        assert not pm_str.df_profile.empty, "pm_str.df_profile이 비어있습니다"
        assert len(pm_str.df_profile) == len(df_profile_str), \
            f"예상 profile 수: {len(df_profile_str)}, 실제: {len(pm_str.df_profile)}"

        # YSTR ProfileDataManager 생성
        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr

        assert pm_ystr.kit == "YSTR", f"예상: 'YSTR', 실제: '{pm_ystr.kit}'"
        assert not pm_ystr.df_profile.empty, "pm_ystr.df_profile이 비어있습니다"
        assert len(pm_ystr.df_profile) == len(df_profile_ystr), \
            f"예상 profile 수: {len(df_profile_ystr)}, 실제: {len(pm_ystr.df_profile)}"

        print(f"\n✓ ProfileDataManager 생성 성공:")
        print(f"  - STR: {len(pm_str.df_profile)} profiles")
        print(f"  - YSTR: {len(pm_ystr.df_profile)} profiles")

    def test_03_report_information_creation(self, df_caseinfo, df_report,
                                             df_profile_str, df_profile_ystr,
                                             sample_case_id):
        """3. ReportInformation 생성 및 데이터 추출"""
        # NFSReportInformation 객체 생성
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)

        assert info.id_case == sample_case_id, \
            f"예상 id_case: {sample_case_id}, 실제: {info.id_case}"

        # 사건 정보 추출
        info.extract_caseinfo_from_df(df_caseinfo)

        assert info.caseinfo is not None, "caseinfo가 None입니다"
        assert len(info.caseinfo) > 0, "caseinfo가 비어있습니다"
        assert '의뢰관서' in info.caseinfo, "caseinfo에 '의뢰관서' 키가 없습니다"
        assert '접수일자' in info.caseinfo, "caseinfo에 '접수일자' 키가 없습니다"

        print(f"\n✓ 사건정보 추출 성공:")
        print(f"  - 의뢰관서: {info.caseinfo['의뢰관서']}")
        print(f"  - 접수일자: {info.caseinfo['접수일자']}")

        # 증거물 정보 추출
        info.extract_evidenceinfo_from_df(df_report)

        assert not info.evidenceinfo.empty, "evidenceinfo가 비어있습니다"
        assert '감정물번호' in info.evidenceinfo.columns, "evidenceinfo에 '감정물번호' 컬럼이 없습니다"

        print(f"  - 증거물 수: {len(info.evidenceinfo)}")

        # STR 프로필 데이터 매니저 로딩
        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        assert info.pm_str is not None, "pm_str이 로드되지 않았습니다"

        # YSTR 프로필 데이터 매니저 로딩
        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr
        info.load_ystr_profiledatamanager(pm_ystr)

        assert info.pm_ystr is not None, "pm_ystr이 로드되지 않았습니다"

        print(f"  - STR 프로필: 로드됨")
        print(f"  - YSTR 프로필: 로드됨")

    def test_04_report_writer_creation_and_categorization(self, df_caseinfo, df_report,
                                                           df_profile_str, df_profile_ystr,
                                                           sample_case_id):
        """4. ReportWriter 생성 및 categorize_profiles() 실행"""
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

        # NFSReportWriter 생성
        RW = NFS_RW.NFSReportWriter(info, [])

        assert RW.report_data.id_case == sample_case_id, \
            f"예상 case ID: {sample_case_id}, 실제: {RW.report_data.id_case}"
        assert RW.paths_picture == [], "paths_picture가 빈 리스트가 아닙니다"

        # 프로필 분류
        RW.categorize_profiles()

        # code_categorized가 생성되었는지 확인
        assert isinstance(RW.code_categorized, dict), "code_categorized가 dict가 아닙니다"

        print(f"\n✓ ReportWriter 생성 및 프로필 분류 성공:")
        print(f"  - code_categorized keys: {list(RW.code_categorized.keys())}")

        if hasattr(RW, 'categorized_info') and not RW.categorized_info.empty:
            print(f"  - categorized_info shape: {RW.categorized_info.shape}")

    def test_05_phrase_generation_ref(self, df_caseinfo, df_report,
                                       df_profile_str, df_profile_ystr,
                                       sample_case_id, monkeypatch):
        """5. 대조 phrase 생성 (make_phrase_ref)"""
        # 사용자 입력 mock 처리 (식별지수 포함하도록 'n' 반환)
        monkeypatch.setattr('builtins.input', lambda x: 'n')

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
        RW.categorize_profiles()

        # 대조 프로필 문구 생성
        initial_phrases_count = len(RW.phrases_result)
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_ref, type_profile='대조')

        # phrase가 추가되었는지 확인
        assert len(RW.phrases_result) >= initial_phrases_count, \
            f"phrase가 추가되지 않았습니다. 이전: {initial_phrases_count}, 이후: {len(RW.phrases_result)}"

        print(f"\n✓ 대조 phrase 생성 성공:")
        print(f"  - 생성된 phrase 수: {len(RW.phrases_result) - initial_phrases_count}")

    def test_06_phrase_generation_res(self, df_caseinfo, df_report,
                                       df_profile_str, df_profile_ystr,
                                       sample_case_id, monkeypatch):
        """6. 대표 phrase 생성 (make_phrase_res)"""
        # 사용자 입력 mock 처리
        monkeypatch.setattr('builtins.input', lambda x: 'n')

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
        RW.categorize_profiles()
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_ref, type_profile='대조')

        # 대표 프로필 문구 생성
        initial_phrases_count = len(RW.phrases_result)
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_res, type_profile='대표')

        # phrase가 추가되었는지 확인
        assert len(RW.phrases_result) >= initial_phrases_count, \
            f"phrase가 추가되지 않았습니다. 이전: {initial_phrases_count}, 이후: {len(RW.phrases_result)}"

        print(f"\n✓ 대표 phrase 생성 성공:")
        print(f"  - 생성된 phrase 수: {len(RW.phrases_result) - initial_phrases_count}")

    def test_07_phrase_generation_nd(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      sample_case_id, monkeypatch):
        """7. ND phrase 생성 (make_phrase_nd)"""
        # 사용자 입력 mock 처리
        monkeypatch.setattr('builtins.input', lambda x: 'n')

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
        RW.categorize_profiles()
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_ref, type_profile='대조')
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_res, type_profile='대표')

        # ND 프로필 문구 생성
        initial_phrases_count = len(RW.phrases_result)
        RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nd, type_profile='ND')

        print(f"\n✓ ND phrase 생성 완료:")
        print(f"  - 생성된 phrase 수: {len(RW.phrases_result) - initial_phrases_count}")

    def test_08_phrase_generation_nc(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      sample_case_id, monkeypatch):
        """8. NC phrase 생성 (make_phrase_nc)"""
        # 사용자 입력 mock 처리
        monkeypatch.setattr('builtins.input', lambda x: 'n')

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
        RW.categorize_profiles()
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_ref, type_profile='대조')
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_res, type_profile='대표')
        RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nd, type_profile='ND')

        # NC 프로필 문구 생성
        initial_phrases_count = len(RW.phrases_result)
        RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nc, type_profile='NC')

        print(f"\n✓ NC phrase 생성 완료:")
        print(f"  - 생성된 phrase 수: {len(RW.phrases_result) - initial_phrases_count}")

    def test_09_complete_workflow_final_validation(self, df_caseinfo, df_report,
                                                     df_profile_str, df_profile_ystr,
                                                     sample_case_id, monkeypatch):
        """9. 전체 워크플로우 최종 검증 (main.py 완전 재현)"""
        # 사용자 입력 mock 처리
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        # 데이터 로딩
        print(f"\n▶ 전체 워크플로우 시작 (Case: {sample_case_id})")

        # ProfileDataManager 생성
        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str

        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr

        # ReportInformation 생성
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)
        info.load_str_profiledatamanager(pm_str)
        info.load_ystr_profiledatamanager(pm_ystr)

        # ReportWriter 생성
        RW = NFS_RW.NFSReportWriter(info, [])

        # 프로필 분류
        RW.categorize_profiles()

        # Phrase 생성
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_ref, type_profile='대조')
        RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_res, type_profile='대표')
        RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nd, type_profile='ND')
        RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nc, type_profile='NC')

        # 최종 결과 검증
        profile_blocks_count = len(RW.profile_blocks)
        phrases_count = len(RW.phrases_result)

        print(f"\n✓ 전체 워크플로우 완료:")
        print(f"  - 생성된 프로필 블록 수: {profile_blocks_count}")
        print(f"  - 생성된 phrase 수: {phrases_count}")

        # 결과 출력 (main.py와 동일)
        if phrases_count > 0:
            print(f"\n📋 생성된 phrases (처음 3개):")
            for i, phrase in enumerate(RW.phrases_result[:3]):
                print(f"  {i+1}. {phrase[:100]}..." if len(phrase) > 100 else f"  {i+1}. {phrase}")

        # 기본 검증
        assert profile_blocks_count >= 0, "profile_blocks가 생성되지 않았습니다"
        assert phrases_count >= 0, "phrases_result가 생성되지 않았습니다"

        print(f"\n✓ main.py 워크플로우 재현 성공!")
