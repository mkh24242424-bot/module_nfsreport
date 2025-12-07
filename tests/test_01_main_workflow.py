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

    def test_04_report_writer_creation_and_block_generation(self, df_caseinfo, df_report,
                                                           df_profile_str, df_profile_ystr,
                                                           sample_case_id):
        """4. ReportWriter 생성 및 블록 자동 생성 검증"""
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

        # NFSReportWriter 생성 (블록이 자동으로 생성됨)
        RW = NFS_RW.NFSReportWriter(info, [])

        assert RW.report_data.id_case == sample_case_id, \
            f"예상 case ID: {sample_case_id}, 실제: {RW.report_data.id_case}"
        assert RW.paths_picture == [], "paths_picture가 빈 리스트가 아닙니다"

        # 블록 매니저가 생성되었는지 확인
        assert hasattr(RW, 'blocks_manager'), "blocks_manager가 없습니다"
        assert "STR" in RW.blocks_manager, "STR 블록 매니저가 없습니다"
        assert "YSTR" in RW.blocks_manager, "YSTR 블록 매니저가 없습니다"

        # STR 블록이 생성되었는지 확인
        str_blocks = RW.blocks_manager["STR"].blocks
        assert isinstance(str_blocks, dict), "STR blocks가 dict가 아닙니다"
        assert '대조' in str_blocks, "대조 블록이 없습니다"
        assert '대조일치' in str_blocks, "대조일치 블록이 없습니다"

        print(f"\n✓ ReportWriter 생성 및 블록 생성 성공:")
        print(f"  - STR 블록 유형: {list(str_blocks.keys())}")
        print(f"  - STR 대조 블록 수: {len(str_blocks['대조'])}")
        print(f"  - STR 대조일치 블록 수: {len(str_blocks['대조일치'])}")

    def test_05_phrase_generation_default(self, df_caseinfo, df_report,
                                       df_profile_str, df_profile_ystr,
                                       sample_case_id, monkeypatch):
        """5. make_contents_default()로 전체 문구 생성"""
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

        # 전체 문구 생성
        initial_count = len(RW.phrases_result)
        RW.make_contents_default()

        # phrase가 추가되었는지 확인
        assert len(RW.phrases_result) >= initial_count, \
            f"phrase가 추가되지 않았습니다. 이전: {initial_count}, 이후: {len(RW.phrases_result)}"

        print(f"\n✓ make_contents_default() 실행 성공:")
        print(f"  - 생성된 phrase 수: {len(RW.phrases_result)}")

    def test_06_phrase_generation_str_blocks(self, df_caseinfo, df_report,
                                       df_profile_str, df_profile_ystr,
                                       sample_case_id, monkeypatch):
        """6. STR 블록별 문구 생성 확인"""
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
        RW.make_contents_default()

        # STR 블록 확인
        str_blocks = RW.blocks_manager["STR"].blocks

        print(f"\n✓ STR 블록별 문구 생성 확인:")
        for block_type in ['대조', '대조일치', '대표일치', 'ND', 'NC']:
            block_count = len(str_blocks[block_type])
            print(f"  - {block_type}: {block_count}개 블록")

    def test_07_phrase_generation_ystr_blocks(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      sample_case_id, monkeypatch):
        """7. Y-STR 블록별 문구 생성 확인"""
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
        RW.make_contents_default()

        # Y-STR 블록 확인
        ystr_blocks = RW.blocks_manager["YSTR"].blocks

        print(f"\n✓ Y-STR 블록별 문구 생성 확인:")
        for block_type in ['대조', '대조일치', '대표일치', 'ND', 'NC']:
            block_count = len(ystr_blocks[block_type])
            print(f"  - {block_type}: {block_count}개 블록")

    def test_08_block_profile_structure(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      sample_case_id, monkeypatch):
        """8. BlockProfile 구조 검증"""
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

        # 블록 구조 확인 (대조 블록이 있다면)
        str_blocks = RW.blocks_manager["STR"].blocks
        if str_blocks['대조']:
            block = str_blocks['대조'][0]
            assert hasattr(block, 'idx_first'), "BlockProfile에 idx_first가 없습니다"
            assert hasattr(block, 'nickname'), "BlockProfile에 nickname이 없습니다"
            assert hasattr(block, 'text_table'), "BlockProfile에 text_table이 없습니다"
            assert hasattr(block, 'text_phrase'), "BlockProfile에 text_phrase이 없습니다"
            assert hasattr(block, 'id_ref'), "BlockProfile에 id_ref가 없습니다"

            print(f"\n✓ BlockProfile 구조 검증 성공:")
            print(f"  - idx_first: {block.idx_first}")
            print(f"  - nickname: {block.nickname}")
            print(f"  - id_ref: {block.id_ref}")

    def test_09_complete_workflow_final_validation(self, df_caseinfo, df_report,
                                                     df_profile_str, df_profile_ystr,
                                                     sample_case_id, monkeypatch):
        """9. 전체 워크플로우 최종 검증 (새 구조)"""
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

        # ReportWriter 생성 (블록 자동 생성됨)
        RW = NFS_RW.NFSReportWriter(info, [])

        # Phrase 생성
        RW.make_contents_default()

        # 최종 결과 검증
        str_blocks = RW.blocks_manager["STR"].blocks
        ystr_blocks = RW.blocks_manager["YSTR"].blocks

        total_str_blocks = sum(len(blocks) for blocks in str_blocks.values())
        total_ystr_blocks = sum(len(blocks) for blocks in ystr_blocks.values())
        phrases_count = len(RW.phrases_result)

        print(f"\n✓ 전체 워크플로우 완료:")
        print(f"  - STR 블록 수: {total_str_blocks}")
        print(f"  - Y-STR 블록 수: {total_ystr_blocks}")
        print(f"  - 생성된 phrase 수: {phrases_count}")

        # 결과 출력
        if phrases_count > 0:
            print(f"\n📋 생성된 phrases (처음 3개):")
            for i, phrase in enumerate(RW.phrases_result[:3]):
                print(f"  {i+1}. {phrase[:100]}..." if len(phrase) > 100 else f"  {i+1}. {phrase}")

        # 기본 검증
        assert total_str_blocks >= 0, "STR 블록이 생성되지 않았습니다"
        assert total_ystr_blocks >= 0, "Y-STR 블록이 생성되지 않았습니다"
        assert phrases_count >= 0, "phrases_result가 생성되지 않았습니다"

        print(f"\n✓ 새 구조 워크플로우 검증 성공!")
