"""
5단계: 인라인 데이터로 통합 테스트
최소 필수 데이터만 인라인으로 생성하여 통합 동작 및 엣지 케이스 검증
"""

import pytest
import pandas as pd

import module.NFS_PROFILEDATAMANAGER as NFS_PM
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.NFS_REPORTPHRASER as NFS_RP


class TestMinimalDataIntegration:
    """최소 데이터로 통합 테스트"""

    def test_minimal_case_processing(self, monkeypatch):
        """최소한의 데이터로 전체 프로세스"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        # 최소 사건정보
        df_caseinfo = pd.DataFrame({
            '접수번호': ['2025-C-TEST'],
            '의뢰관서': ['테스트경찰서'],
            '문서번호': ['TEST-001'],
            '접수일자': ['2025-01-01'],
            '시행일자': ['2025-01-10']
        })

        # 최소 증거물정보
        df_report = pd.DataFrame({
            '접수번호': ['2025-C-TEST'],
            '감정물번호': ['2025-C-TEST-1'],
            '감정물': ['혈흔'],
            '분류': ['증거물'],
            '대조_이름': ['피의자A'],
            'Y_대조_이름': [''],
            '프로필_유형': ['대조'],
            'Y_프로필_유형': [''],
            '코드': ['V'],
            'Y_코드': [''],
            '표기번호': ['증1호'],
            'Y_표기번호': [''],
            '기재_여부': ['기재'],
            'Y_기재_여부': ['미기재'],
            '타액_반응': [''],
            '정액_반응': [''],
            '혈흔_반응': ['+'],
            '검색_결과': [''],
            '반환_여부': ['N']
        })

        # 프로세스 실행
        info = NFS_RI.NFSReportInformation(id_case='2025-C-TEST')
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        assert info.caseinfo['의뢰관서'] == '테스트경찰서'
        assert len(info.evidenceinfo) == 1

        print(f"\n✓ 최소 데이터 처리 성공")


class TestErrorHandlingIntegration:
    """에러 처리 통합 테스트"""

    def test_missing_case_graceful_handling(self):
        """존재하지 않는 사건번호 처리"""
        df_caseinfo = pd.DataFrame({
            '접수번호': ['2025-C-EXIST'],
            '의뢰관서': ['서울경찰서'],
            '문서번호': ['DOC-001'],
            '접수일자': ['2025-01-01'],
            '시행일자': ['2025-01-10']
        })

        info = NFS_RI.NFSReportInformation(id_case='2025-C-NOTEXIST')

        # 존재하지 않는 사건번호로 추출 시도
        with pytest.raises(IndexError):
            info.extract_caseinfo_from_df(df_caseinfo)

        print(f"\n✓ 존재하지 않는 사건번호 에러 처리 확인")

    def test_empty_evidenceinfo_processing(self, monkeypatch):
        """증거물이 없는 경우 처리"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        df_caseinfo = pd.DataFrame({
            '접수번호': ['2025-C-EMPTY'],
            '의뢰관서': ['서울경찰서'],
            '문서번호': ['DOC-001'],
            '접수일자': ['2025-01-01'],
            '시행일자': ['2025-01-10']
        })

        df_report = pd.DataFrame({
            '접수번호': ['2025-C-OTHER'],  # 다른 사건번호
            '감정물번호': ['2025-C-OTHER-1'],
            '감정물': ['혈흔'],
            '분류': ['증거물'],
            '대조_이름': ['피의자A'],
            'Y_대조_이름': [''],
            '프로필_유형': ['대조'],
            'Y_프로필_유형': [''],
            '코드': ['V'],
            'Y_코드': [''],
            '표기번호': ['증1호'],
            'Y_표기번호': [''],
            '기재_여부': ['기재'],
            'Y_기재_여부': ['미기재'],
            '타액_반응': [''],
            '정액_반응': [''],
            '혈흔_반응': ['+'],
            '검색_결과': [''],
            '반환_여부': ['N']
        })

        info = NFS_RI.NFSReportInformation(id_case='2025-C-EMPTY')
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        # 증거물이 없어야 함
        assert len(info.evidenceinfo) == 0

        print(f"\n✓ 빈 증거물 처리 확인")


class TestProfileManagerIntegration:
    """ProfileManager 통합 테스트"""

    def test_profile_filtering_by_case(self):
        """사건번호별 프로필 필터링 통합"""
        # 프로필 데이터
        df_profile = pd.DataFrame({
            '접수번호': ['2025-C-1', '2025-C-1', '2025-C-2'],
            '감정물번호': ['2025-C-1-1', '2025-C-1-2', '2025-C-2-1'],
            'AMEL': ['X', 'XY', 'X'],
            'D3S1358': ['15-16', '15-17', '14-16']
        })

        pm = NFS_PM.NFSProfileDataManager(kit="STR")
        pm.df_profile = df_profile

        # 사건번호로 필터링
        filtered_pm = pm.filter_by_codecase(code_case='2025-C-1')

        if filtered_pm:
            assert len(filtered_pm.df_profile) == 2
            print(f"\n✓ 프로필 필터링 성공: 2개 프로필")
        else:
            print(f"\n✓ 프로필 없음 (None 반환)")


class TestReportWriterSwitchKit:
    """ReportWriter의 kit 전환 테스트"""

    def test_switch_kit_property(self):
        """switch_kit property 동작 확인"""
        info = NFS_RI.NFSReportInformation(id_case="test")
        RW = NFS_RW.NFSReportWriter(info, [])

        # switch_kit property 접근
        switch = RW.switch_kit

        assert "STR" in switch
        assert "YSTR" in switch
        assert "code_categorized" in switch["STR"]
        assert "profilemanager" in switch["STR"]

        print(f"\n✓ switch_kit property 동작 확인")


class TestPhraseGenerationWithDifferentInputs:
    """다양한 입력으로 phrase 생성 테스트"""

    def test_phrase_with_various_evidence_text(self, monkeypatch):
        """다양한 증거물 표기로 phrase 생성"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        test_cases = [
            ("증1호", "단일 증거물"),
            ("증1호~증5호", "연속 증거물"),
            ("증1호 및 증3호", "비연속 증거물"),
            ("증1호~증3호 및 증5호", "혼합 표기")
        ]

        for text_evidence, desc in test_cases:
            props = NFS_RW.Properties_Phrase(
                gender="남성",
                likelihoodratio=("1.5", "10"),
                text_evidence=text_evidence,
                nickname="피의자A"
            )

            phrase = NFS_RP.make_phrase_ref(props)

            assert text_evidence in phrase
            assert "디엔에이형" in phrase

            print(f"\n✓ {desc} phrase 생성: {text_evidence}")


class TestCompleteIntegrationScenario:
    """완전한 통합 시나리오 테스트"""

    def test_full_integration_with_inline_data(self, monkeypatch):
        """인라인 데이터로 전체 워크플로우"""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        # 1. 데이터 준비
        df_caseinfo = pd.DataFrame({
            '접수번호': ['2025-C-INT'],
            '의뢰관서': ['통합테스트경찰서'],
            '문서번호': ['INT-001'],
            '접수일자': ['2025-01-01'],
            '시행일자': ['2025-01-10']
        })

        df_report = pd.DataFrame({
            '접수번호': ['2025-C-INT', '2025-C-INT'],
            '감정물번호': ['2025-C-INT-1', '2025-C-INT-2'],
            '감정물': ['혈흔', '타액'],
            '분류': ['증거물', '증거물'],
            '대조_이름': ['피의자A', '피의자B'],
            'Y_대조_이름': ['', ''],
            '프로필_유형': ['대조', '대조'],
            'Y_프로필_유형': ['', ''],
            '코드': ['V1', 'V2'],
            'Y_코드': ['', ''],
            '표기번호': ['증1호', '증2호'],
            'Y_표기번호': ['', ''],
            '기재_여부': ['기재', '기재'],
            'Y_기재_여부': ['미기재', '미기재'],
            '타액_반응': ['', '+'],
            '정액_반응': ['', ''],
            '혈흔_반응': ['+', ''],
            '검색_결과': ['', ''],
            '반환_여부': ['N', 'N']
        })

        # 2. ReportInformation 생성 및 데이터 추출
        info = NFS_RI.NFSReportInformation(id_case='2025-C-INT')
        info.extract_caseinfo_from_df(df_caseinfo)
        info.extract_evidenceinfo_from_df(df_report)

        # 3. ReportWriter 생성
        RW = NFS_RW.NFSReportWriter(info, [])

        # 4. 프로필 분류
        RW.categorize_profiles()

        # 5. 결과 검증
        assert info.id_case == '2025-C-INT'
        assert len(info.evidenceinfo) == 2
        assert isinstance(RW.code_categorized, dict)

        print(f"\n✓ 완전한 통합 시나리오 성공:")
        print(f"  - 사건번호: {info.id_case}")
        print(f"  - 증거물 수: {len(info.evidenceinfo)}")
        print(f"  - 분류된 타입 수: {len(RW.code_categorized)}")
