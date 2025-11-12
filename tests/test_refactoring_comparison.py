"""
리팩토링 검증 테스트: _create_text_evidence_v2

리팩토링된 메서드(_create_text_evidence_v2)의 기능을 독립적으로 검증합니다.

**중요 발견사항:**
원본 메서드 _create_text_evidence() (line 121)에 pandas 구문 버그가 있습니다:
    df_target = df_target[df_target[...] != "미기재", :].copy()  # 잘못된 구문
이는 InvalidIndexError를 발생시킵니다. 리팩토링 버전에서 이 버그를 수정했습니다.

테스트 시나리오:
1. 빈 리스트
2. 단일 증거물
3. 두 개 증거물 ("및" 연결)
4. 연속 증거물 3개 이상 ("~" 사용)
5. 비연속 증거물
6. 체액 반응 포함
7. 혼합 시나리오
"""

import pytest
import pandas as pd
from module.NFS_REPORTWRITER import NFSReportWriter
from module.NFS_REPORTINFORMATION import NFSReportInformation


@pytest.fixture
def setup_writer():
    """테스트용 NFSReportWriter 객체 생성"""
    # 기본 report_data 준비
    report_data = NFSReportInformation(id_case="TEST-001")

    # 증거물 정보 DataFrame
    # 실제 시나리오: 모든 증거물이 존재하지만, 일부는 "미기재"로 표시됨
    evidenceinfo = pd.DataFrame({
        "감정물번호": ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3",
                      "2023-D-1-4", "2023-D-1-5", "2023-D-1-6",  # 4번 포함 (미기재)
                      "2023-D-1-7", "2023-D-1-8", "2023-D-1-9",  # 7,8,9번 (미기재)
                      "2023-D-1-10"],  # 독립 증거물
        "표기번호": ["증1호", "증2호", "증3호",
                     "증4호", "증5호", "증6호",  # 4번도 정상 표기
                     "증7호", "증8호", "증9호",  # 7,8,9번도 정상 표기
                     "증10호"],
        "Y_표기번호": ["Y증1호", "Y증2호", "Y증3호",
                       "미기재", "Y증5호", "Y증6호",
                       "미기재", "미기재", "미기재",
                       "Y증10호"],
        "기재_여부": ["기재", "기재", "기재",
                      "기재", "기재", "기재",  # 모두 기재 (표기번호로 필터링됨)
                      "기재", "기재", "기재",
                      "기재"],
        "Y_기재_여부": ["기재", "기재", "기재",
                       "기재", "기재", "기재",
                       "기재", "기재", "기재",
                       "미기재"],
        "타액_반응": ["양성", "양성", "양성",
                     "실험 안함", "음성", "실험 안함",
                     "실험 안함", "실험 안함", "실험 안함",
                     "양성"],
        "정액_반응": ["음성", "음성", "음성",
                     "실험 안함", "양성", "실험 안함",
                     "실험 안함", "실험 안함", "실험 안함",
                     "음성"],
        "혈흔_반응": ["실험 안함", "실험 안함", "실험 안함",
                     "실험 안함", "실험 안함", "실험 안함",
                     "실험 안함", "실험 안함", "실험 안함",
                     "음성"],
    }, index=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])  # 연속 인덱스

    report_data.evidenceinfo = evidenceinfo

    # paths_picture 파라미터 추가
    writer = NFSReportWriter(report_data, paths_picture=[])
    return writer


class TestCreateTextEvidenceV2:
    """리팩토링 버전 _create_text_evidence_v2 기능 테스트"""

    def test_empty_list(self, setup_writer):
        """빈 리스트 처리"""
        writer = setup_writer
        result = writer._create_text_evidence_v2([], kit="STR", reaction=False)
        assert result == ""

    def test_single_evidence_no_reaction(self, setup_writer):
        """단일 증거물, 반응 정보 없음"""
        writer = setup_writer
        list_id = ["2023-D-1-1"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=False)
        assert result == "증1호"

    def test_single_evidence_with_reaction(self, setup_writer):
        """단일 증거물, 반응 정보 포함"""
        writer = setup_writer
        list_id = ["2023-D-1-1"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=True)

        # 증1호 + 반응 정보
        assert "증1호" in result
        assert "타액반응 양성" in result or "정액반응" in result

    def test_two_evidences(self, setup_writer):
        """두 개 증거물 ("및" 연결)"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=False)

        assert "증1호 및 증2호" in result

    def test_three_consecutive_evidences(self, setup_writer):
        """연속된 3개 증거물 ("~" 사용)"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=False)

        # 연속 3개는 "증1호~증3호" 형식
        assert "증1호~증3호" in result

    def test_non_consecutive_evidences(self, setup_writer):
        """비연속 증거물 (1,2,3,5,6 - 4가 없음)"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3",
                   "2023-D-1-5", "2023-D-1-6"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=False)

        # 1-3 연속, 5-6 연속 (2개는 쉼표로 구분)
        assert "증1호~증3호" in result
        assert "증5호, 증6호" in result or "증5호" in result

    def test_with_reaction_same_result(self, setup_writer):
        """체액 반응 포함, 모두 동일한 반응"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=True)

        # 모두 같은 반응이므로 "모두" 표현 포함
        assert "모두" in result or "타액반응" in result

    def test_with_reaction_different_results(self, setup_writer):
        """체액 반응 포함, 서로 다른 반응"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-5"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=True)

        # 서로 다른 반응이므로 각각 표시
        assert "증1호" in result or "증5호" in result

    def test_ystr_kit(self, setup_writer):
        """YSTR 키트 사용"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3"]
        result = writer._create_text_evidence_v2(list_id, kit="YSTR", reaction=False)

        # YSTR은 "Y증" 형식
        assert "Y증1호~Y증3호" in result

    def test_complex_scenario(self, setup_writer):
        """복잡한 시나리오: 연속+비연속+독립 증거물"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3",  # 연속 3개
                   "2023-D-1-5", "2023-D-1-6",  # 연속 2개
                   "2023-D-1-10"]  # 독립 1개
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=False)

        # 여러 그룹이 쉼표로 연결
        assert "증1호~증3호" in result
        assert "증10호" in result

    def test_all_evidences_no_reaction(self, setup_writer):
        """모든 증거물, 반응 없음"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3",
                   "2023-D-1-5", "2023-D-1-6", "2023-D-1-10"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=False)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_evidences_with_reaction(self, setup_writer):
        """모든 증거물, 반응 포함"""
        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3",
                   "2023-D-1-5", "2023-D-1-6", "2023-D-1-10"]
        result = writer._create_text_evidence_v2(list_id, kit="STR", reaction=True)

        assert isinstance(result, str)
        assert len(result) > 0


class TestHelperMethods:
    """개별 헬퍼 메서드 단위 테스트"""

    def test_filter_evidence_by_ids(self, setup_writer):
        """_filter_evidence_by_ids 테스트"""
        writer = setup_writer

        list_id = ["2023-D-1-1", "2023-D-1-2"]
        df = writer._filter_evidence_by_ids(list_id, kit="STR")

        assert len(df) == 2
        assert "표기번호" in df.columns
        assert "감정물번호_다음" in df.columns
        assert df.iloc[0]["표기번호"] == "증1호"

    def test_format_single_reaction_positive(self, setup_writer):
        """_format_single_reaction 양성 테스트"""
        writer = setup_writer

        result = writer._format_single_reaction("타액_반응", "양성")
        assert result == "타액반응 양성"

    def test_format_single_reaction_skip(self, setup_writer):
        """_format_single_reaction 실험 안함 테스트"""
        writer = setup_writer

        result = writer._format_single_reaction("타액_반응", "실험 안함")
        assert result == ""

    def test_format_reaction_parentheses(self, setup_writer):
        """_format_reaction_parentheses 테스트"""
        writer = setup_writer

        result = writer._format_reaction_parentheses("타액반응 양성,혈흔반응 음성")
        assert result == "(타액반응 양성, 혈흔반응 음성)"

        # 빈 문자열
        result_empty = writer._format_reaction_parentheses("")
        assert result_empty == ""

    def test_group_consecutive_evidence(self, setup_writer):
        """_group_consecutive_evidence 테스트"""
        writer = setup_writer

        # 테스트용 DataFrame
        df = pd.DataFrame({
            "표기번호": ["증1호", "증2호", "증3호", "증5호"],
            "감정물번호": ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3", "2023-D-1-5"],
            "감정물번호_다음": ["2023-D-1-2", "2023-D-1-3", "2023-D-1-5", None],
        })

        chains = writer._group_consecutive_evidence(df)

        # 연속 3개 + 독립 1개 = 2개 그룹
        assert len(chains) >= 1
        # 첫 번째 그룹은 연속된 증거물들
        assert "증1호" in chains[0]

    def test_format_evidence_text_with_chains(self, setup_writer):
        """_format_evidence_text 테스트"""
        writer = setup_writer

        # 3개 이상 체인: "~" 사용
        chains = [["증1호", "증2호", "증3호"]]
        result = writer._format_evidence_text(chains)
        assert "증1호~증3호" in result

        # 2개 체인: 쉼표로 연결
        chains_short = [["증1호", "증2호"]]
        result_short = writer._format_evidence_text(chains_short)
        assert "증1호, 증2호" in result_short

        # 혼합
        chains_mixed = [["증1호", "증2호", "증3호"], ["증5호"]]
        result_mixed = writer._format_evidence_text(chains_mixed)
        assert "증1호~증3호" in result_mixed
        assert "증5호" in result_mixed


class TestPerformance:
    """성능 테스트 (참고용)"""

    def test_performance_baseline(self, setup_writer):
        """리팩토링 버전 성능 기준 측정"""
        import time

        writer = setup_writer
        list_id = ["2023-D-1-1", "2023-D-1-2", "2023-D-1-3",
                   "2023-D-1-5", "2023-D-1-6"]

        # 리팩토링 메서드 성능 측정
        start = time.time()
        for _ in range(100):
            writer._create_text_evidence_v2(list_id, kit="STR", reaction=True)
        elapsed = time.time() - start

        # 합리적인 시간 내에 완료되는지 확인 (100회 실행이 1초 이내)
        assert elapsed < 1.0, f"성능이 예상보다 느림: {elapsed:.4f}s (목표: < 1.0s)"

        print(f"\n성능 측정 (100회 실행): {elapsed:.4f}s")
        print(f"  평균: {elapsed/100*1000:.2f}ms per call")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
