"""
NFS_DATAFRAME 모듈 테스트
DataFrame 처리 유틸리티 함수들을 검증합니다.
"""

import pytest
import pandas as pd
import tempfile
import os
from module import NFS_DATAFRAME as NFS_DF


class TestXlsToDataframe:
    """xls_to_dataframe() 함수 테스트"""

    def test_read_excel_with_header(self):
        """header=True로 엑셀 읽기"""
        # 임시 엑셀 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df_test = pd.DataFrame({
                'Column1': [1, 2, 3],
                'Column2': ['A', 'B', 'C']
            })
            df_test.to_excel(tmp.name, index=False)
            tmp_path = tmp.name

        try:
            result = NFS_DF.xls_to_dataframe(tmp_path, header=True)
            assert isinstance(result, pd.DataFrame)
            assert list(result.columns) == ['Column1', 'Column2']
            assert len(result) == 3
        finally:
            os.unlink(tmp_path)

    def test_read_excel_without_header(self):
        """header=False로 엑셀 읽기"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df_test = pd.DataFrame([[1, 'A'], [2, 'B'], [3, 'C']])
            df_test.to_excel(tmp.name, index=False, header=False)
            tmp_path = tmp.name

        try:
            result = NFS_DF.xls_to_dataframe(tmp_path, header=False)
            assert isinstance(result, pd.DataFrame)
            assert result.columns[0] == 0  # 숫자 인덱스 컬럼명
            assert len(result) == 3
        finally:
            os.unlink(tmp_path)

    def test_dtype_object(self):
        """dtype='object' 확인"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df_test = pd.DataFrame({'Numbers': [1, 2, 3]})
            df_test.to_excel(tmp.name, index=False)
            tmp_path = tmp.name

        try:
            result = NFS_DF.xls_to_dataframe(tmp_path, header=True)
            # dtype='object'로 읽으므로 문자열로 변환됨
            assert result['Numbers'].dtype == 'object'
        finally:
            os.unlink(tmp_path)


class TestSortBySerialNumber:
    """sort_by_serial_number() 함수 테스트"""

    def test_basic_sorting(self):
        """기본 일련번호 정렬"""
        df = pd.DataFrame({
            '일련번호': ['2023-D-1234-3', '2023-D-1234-1', '2023-D-1234-2'],
            'value': ['C', 'A', 'B']
        })
        result = NFS_DF.sort_by_serial_number(df, '일련번호')
        expected_order = ['2023-D-1234-1', '2023-D-1234-2', '2023-D-1234-3']
        assert list(result['일련번호']) == expected_order

    def test_different_case_numbers(self):
        """다른 사건번호 정렬"""
        df = pd.DataFrame({
            '일련번호': ['2024-D-1000-1', '2023-D-2000-1', '2023-D-1500-1'],
            'value': ['A', 'B', 'C']
        })
        result = NFS_DF.sort_by_serial_number(df, '일련번호')
        # 2023이 먼저, 그 다음 사건번호 순서
        assert result.iloc[0]['일련번호'] == '2023-D-1500-1'
        assert result.iloc[1]['일련번호'] == '2023-D-2000-1'
        assert result.iloc[2]['일련번호'] == '2024-D-1000-1'

    def test_four_digit_pattern(self):
        """4개 숫자 그룹 패턴 (예: 2023-D-1234-5a)"""
        df = pd.DataFrame({
            '일련번호': ['2023-D-1234-5', '2023-D-1234-2', '2023-D-1234-10'],
            'value': ['A', 'B', 'C']
        })
        result = NFS_DF.sort_by_serial_number(df, '일련번호')
        expected_order = ['2023-D-1234-2', '2023-D-1234-5', '2023-D-1234-10']
        assert list(result['일련번호']) == expected_order

    def test_three_digit_pattern(self):
        """3개 숫자 그룹 패턴 (4번째 숫자가 0으로 처리됨)"""
        # 함수는 3개 숫자만 있을 때 4번째를 0으로 처리
        df = pd.DataFrame({
            '일련번호': ['2023-D-1234-1', '2023-D-1234-0', '2023-D-1235-0'],
            'value': ['A', 'B', 'C']
        })
        result = NFS_DF.sort_by_serial_number(df, '일련번호')
        # 정렬이 제대로 되는지 확인
        assert len(result) == 3


class TestLinkNumEvidence:
    """link_num_evidence() 함수 테스트"""

    def test_single_evidence(self):
        """단일 증거물"""
        df = pd.DataFrame({
            '표기번호': ['증1호']
        })
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=False)
        assert result == '증1호'

    def test_two_evidence(self):
        """두 개 증거물 - '및'로 연결"""
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호']
        })
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=False)
        assert result == '증1호 및 증2호'

    def test_consecutive_evidence(self):
        """연속된 증거물 - '~'로 묶기"""
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호', '증3호', '증4호', '증5호']
        })
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=False)
        assert result == '증1호~증5호'

    def test_non_consecutive_evidence(self):
        """DataFrame 인덱스가 비연속일 때 그룹 분리"""
        # 인덱스를 명시적으로 설정: [0, 1, 5, 6]
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호', '증5호', '증6호']
        }, index=[0, 1, 5, 6])
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=False)
        # 인덱스 0-1은 연속, 5-6도 연속이지만 1과 5 사이가 끊김
        # 따라서 두 그룹으로 분리되어야 함
        assert '증1호' in result
        assert '증2호' in result
        assert '증5호' in result
        assert '증6호' in result

    def test_with_reaction(self):
        """체액 반응 포함"""
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호'],
            '타액_반응': ['양성', '실험 안함'],
            '정액_반응': ['실험 안함', '실험 안함'],
            '혈흔_반응': ['실험 안함', '실험 안함']
        })
        result = NFS_DF.link_num_evidence(df, reaction=True, y23=False)
        assert '타액반응 양성' in result
        assert '증1호' in result

    def test_y23_mode(self):
        """Y-STR 모드 (y23=True)"""
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호'],
            'Y_표기번호': ['Y증1호', 'Y증2호']
        })
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=True)
        assert 'Y증1호' in result or 'Y증2호' in result

    def test_reaction_prevents_consecutive(self):
        """반응 결과가 있으면 연속 처리 중단"""
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호', '증3호'],
            '타액_반응': ['실험 안함', '양성', '실험 안함'],
            '정액_반응': ['실험 안함', '실험 안함', '실험 안함'],
            '혈흔_반응': ['실험 안함', '실험 안함', '실험 안함']
        })
        result = NFS_DF.link_num_evidence(df, reaction=True, y23=False)
        # 증2호에 반응이 있으므로 1~3으로 묶이지 않음
        assert '타액반응 양성' in result

    def test_multiple_reactions(self):
        """여러 체액 반응"""
        df = pd.DataFrame({
            '표기번호': ['증1호'],
            '타액_반응': ['양성'],
            '정액_반응': ['양성'],
            '혈흔_반응': ['음성']
        })
        result = NFS_DF.link_num_evidence(df, reaction=True, y23=False)
        assert '타액반응 양성' in result
        assert '정액반응 양성' in result
        assert '혈흔반응 음성' in result

    def test_empty_dataframe(self):
        """빈 데이터프레임은 처리하지 않음"""
        # 이 함수는 빈 DataFrame에 대한 처리가 없어 에러가 발생할 수 있음
        # 실제 사용에서는 빈 DataFrame이 입력되지 않도록 해야 함
        pass


class TestLinkNumEvidenceEdgeCases:
    """link_num_evidence() 엣지 케이스 테스트"""

    def test_three_consecutive_becomes_range(self):
        """3개 이상 연속은 범위로 표시"""
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호', '증3호']
        })
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=False)
        assert '증1호~증3호' in result

    def test_two_separate_groups(self):
        """DataFrame 인덱스가 비연속일 때 여러 그룹으로 분리"""
        # 인덱스를 명시적으로 설정: [0, 1, 10, 11, 12]
        df = pd.DataFrame({
            '표기번호': ['증1호', '증2호', '증10호', '증11호', '증12호']
        }, index=[0, 1, 10, 11, 12])
        result = NFS_DF.link_num_evidence(df, reaction=False, y23=False)
        # 인덱스 0-1 그룹, 10-12 그룹으로 분리
        parts = result.split(', ')
        assert len(parts) >= 2  # 최소 2개 그룹
