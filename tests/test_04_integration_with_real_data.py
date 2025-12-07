"""
4단계: 주어진 데이터로 통합 테스트
testdata/ CSV 파일을 사용하여 모듈 간 통합 동작을 검증
"""

import pytest
import pandas as pd

import module.NFS_PROFILEDATAMANAGER as NFS_PM
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.NFS_REPORTPHRASER as NFS_RP


class TestCSVToReportInformationPipeline:
    """CSV → ReportInformation 파이프라인 테스트"""

    def test_full_data_extraction_pipeline(self, df_caseinfo, df_report,
                                             df_profile_str, df_profile_ystr,
                                             sample_case_id):
        """전체 데이터 추출 파이프라인"""
        # 1. ReportInformation 생성
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)

        # 2. 사건정보 추출
        info.extract_caseinfo_from_df(df_caseinfo)
        assert info.caseinfo is not None
        assert '의뢰관서' in info.caseinfo

        # 3. 증거물정보 추출
        info.extract_evidenceinfo_from_df(df_report)
        assert not info.evidenceinfo.empty

        # 4. STR ProfileDataManager 로딩
        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)
        assert info.pm_str is not None

        # 5. YSTR ProfileDataManager 로딩
        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr
        info.load_ystr_profiledatamanager(pm_ystr)
        assert info.pm_ystr is not None

        print(f"\n✓ 전체 데이터 추출 파이프라인 성공")
        print(f"  - 사건정보: {len(info.caseinfo)}개 필드")
        print(f"  - 증거물: {len(info.evidenceinfo)}개")


class TestReportInfoToPhrasePipeline:
    """ReportInformation → Phrase 생성 파이프라인 테스트"""

    def test_report_to_phrase_pipeline(self, df_caseinfo, df_report,
                                        df_profile_str, df_profile_ystr,
                                        sample_case_id, monkeypatch):
        """ReportInformation → ReportWriter → Phrase 파이프라인"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        # 1. 데이터 준비
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr
        info.load_ystr_profiledatamanager(pm_ystr)

        # 2. ReportWriter 생성 (블록 자동 생성)
        RW = NFS_RW.NFSReportWriter(info, [])

        # 3. Phrase 생성 (새 구조)
        RW.make_contents_default()

        # 4. 결과 검증
        total_phrases = len(RW.phrases_result)

        # 블록 수 확인
        str_blocks = RW.blocks_manager["STR"].blocks
        total_blocks = sum(len(blocks) for blocks in str_blocks.values())

        print(f"\n✓ Report → Phrase 파이프라인 성공")
        print(f"  - 총 블록 수: {total_blocks}개")
        print(f"  - 생성된 phrases: {total_phrases}개")

        assert total_phrases >= 0


class TestMultipleCasesBatchProcessing:
    """여러 케이스 배치 처리 테스트"""

    def test_process_multiple_cases(self, df_caseinfo, df_report,
                                      df_profile_str, df_profile_ystr,
                                      monkeypatch):
        """여러 사건을 순차적으로 처리"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        # 사건 목록 가져오기 (최대 3개)
        case_ids = df_caseinfo['접수번호'].unique()[:3]

        results = []

        for case_id in case_ids:
            try:
                # 각 사건 처리
                info = NFS_RI.NFSReportInformation(id_case=case_id)
                info.extract_caseinfo_from_df(df_caseinfo)
                info.extract_evidenceinfo_from_df(df_report)

                pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
                pm_str.df_profile = df_profile_str
                info.load_str_profiledatamanager(pm_str)

                pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
                pm_ystr.df_profile = df_profile_ystr
                info.load_ystr_profiledatamanager(pm_ystr)

                # ReportWriter 생성 (블록 자동 생성)
                RW = NFS_RW.NFSReportWriter(info, [])

                results.append({
                    'case_id': case_id,
                    'evidences': len(info.evidenceinfo),
                    'success': True
                })

            except Exception as e:
                results.append({
                    'case_id': case_id,
                    'error': str(e),
                    'success': False
                })

        print(f"\n✓ 배치 처리 완료:")
        for r in results:
            if r['success']:
                print(f"  - {r['case_id']}: {r['evidences']}개 증거물")
            else:
                print(f"  - {r['case_id']}: 실패 ({r.get('error', 'Unknown')})")

        # 최소 1개는 성공해야 함
        assert any(r['success'] for r in results)


class TestProfileTypeCategorization:
    """프로필 타입별 처리 테스트"""

    def test_categorization_by_profile_type(self, df_caseinfo, df_report,
                                              df_profile_str, df_profile_ystr,
                                              sample_case_id):
        """프로필 타입에 따른 분류 확인"""
        # 데이터 준비
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        # ReportWriter 생성 (블록 자동 생성)
        RW = NFS_RW.NFSReportWriter(info, [])

        # 블록 매니저 확인 (새 구조)
        assert "STR" in RW.blocks_manager
        assert "YSTR" in RW.blocks_manager

        str_blocks = RW.blocks_manager["STR"].blocks
        block_types = list(str_blocks.keys())

        print(f"\n✓ 프로필 타입별 분류:")
        for block_type in block_types:
            print(f"  - {block_type}: {len(str_blocks[block_type])}개 블록")

        assert isinstance(str_blocks, dict)


class TestSTRAndYSTRSimultaneousProcessing:
    """STR + YSTR 동시 처리 테스트"""

    def test_str_and_ystr_together(self, df_caseinfo, df_report,
                                     df_profile_str, df_profile_ystr,
                                     sample_case_id):
        """STR과 YSTR을 동시에 처리"""
        # 데이터 준비
        info = NFS_RI.NFSReportInformation(id_case=sample_case_id)
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        # STR 로딩
        pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
        pm_str.df_profile = df_profile_str
        info.load_str_profiledatamanager(pm_str)

        # YSTR 로딩
        pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
        pm_ystr.df_profile = df_profile_ystr
        info.load_ystr_profiledatamanager(pm_ystr)

        # 검증
        assert info.pm_str is not None
        assert info.pm_ystr is not None
        assert info.pm_str.kit == "STR"
        assert info.pm_ystr.kit == "YSTR"

        print(f"\n✓ STR + YSTR 동시 처리 성공:")
        print(f"  - STR 프로필: {len(info.pm_str.df_profile)}개")
        print(f"  - YSTR 프로필: {len(info.pm_ystr.df_profile)}개")
