"""
NFS_PROFILEDATAMANAGER 모듈 테스트
NFSProfileDataManager 클래스의 기능을 검증합니다.
"""

import pytest
import pandas as pd
import tempfile
import os
from module.NFS_PROFILEDATAMANAGER import NFSProfileDataManager
from module.NFS_STRPROFILE import STRProfile


class TestNFSProfileDataManagerInit:
    """NFSProfileDataManager 초기화 테스트"""

    def test_default_initialization(self):
        """기본 초기화 (STR 키트)"""
        pdm = NFSProfileDataManager()
        assert pdm.kit == "STR"
        assert isinstance(pdm.df_profile, pd.DataFrame)
        assert pdm.df_profile.empty
        assert isinstance(pdm.allele_frequency, pd.DataFrame)
        assert not pdm.allele_frequency.empty  # CSV 파일 로드됨

    def test_initialization_with_ystr(self):
        """Y-STR 키트로 초기화"""
        pdm = NFSProfileDataManager(kit="YSTR")
        assert pdm.kit == "YSTR"
        assert pdm.df_profile.empty

    def test_dict_markers_exists(self):
        """DICT_MARKERS 상수 확인"""
        pdm = NFSProfileDataManager()
        assert "STR" in pdm.DICT_MARKERS
        assert "YSTR" in pdm.DICT_MARKERS
        assert isinstance(pdm.DICT_MARKERS["STR"], list)
        assert isinstance(pdm.DICT_MARKERS["YSTR"], list)
        assert len(pdm.DICT_MARKERS["STR"]) == 24
        assert len(pdm.DICT_MARKERS["YSTR"]) == 20


class TestGenerateSTRProfile:
    """generate_STRProfile() 메서드 테스트"""

    def test_generate_profile_basic(self):
        """기본 프로파일 생성"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': ['XY'],
            'D3S1358': ['15-16'],
            'vWA': ['14-17']
        })

        profile = pdm.generate_STRProfile('2023-D-1234-1')

        assert isinstance(profile, STRProfile)
        assert profile.id == '2023-D-1234-1'
        assert profile.profile['D3S1358'] == {'15', '16'}
        assert profile.profile['vWA'] == {'14', '17'}

    def test_generate_profile_str_20(self):
        """STR_20=True로 프로파일 생성"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': ['XY']
        })
        # 나머지 마커들은 빈 문자열로
        for marker in pdm.DICT_MARKERS["STR"]:
            if marker not in pdm.df_profile.columns:
                pdm.df_profile[marker] = ['']

        profile = pdm.generate_STRProfile('2023-D-1234-1', STR_20=True)

        assert isinstance(profile, STRProfile)
        # STR_20=True이면 마지막 3개 마커 제외

    def test_generate_profile_nonexistent_sample(self):
        """존재하지 않는 샘플명으로 ValueError 발생"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': ['XY']
        })

        with pytest.raises(ValueError):
            pdm.generate_STRProfile('nonexistent-sample')


class TestGenerateEmptySTRProfile:
    """generate_empty_STRProfile() 메서드 테스트"""

    def test_generate_empty_profile(self):
        """빈 프로파일 생성"""
        pdm = NFSProfileDataManager(kit="STR")
        profile = pdm.generate_empty_STRProfile(samplename="empty")

        assert isinstance(profile, STRProfile)
        assert profile.id == "empty"
        assert len(profile.profile) == 24  # STR 마커 24개
        # 모든 마커가 빈 set
        for marker, alleles in profile.profile.items():
            assert alleles == set()

    def test_generate_empty_profile_ystr(self):
        """Y-STR 빈 프로파일 생성"""
        pdm = NFSProfileDataManager(kit="YSTR")
        profile = pdm.generate_empty_STRProfile(samplename="empty_ystr")

        assert isinstance(profile, STRProfile)
        assert len(profile.profile) == 20  # Y-STR 마커 20개


class TestUpdateProfile:
    """update_profile_with_STRProfile() 메서드 테스트"""

    def test_update_existing_profile(self):
        """기존 프로파일 업데이트"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': [''],
            'D3S1358': [''],
            'vWA': ['']
        })

        new_profile = STRProfile(
            id='2023-D-1234-1',
            profile={
                'D3S1358': {'15', '16'},
                'vWA': {'14', '17'}
            }
        )

        pdm.update_profile_with_STRProfile('2023-D-1234-1', new_profile)

        assert pdm.df_profile.loc[0, 'D3S1358'] == '15-16'
        assert pdm.df_profile.loc[0, 'vWA'] == '14-17'

    def test_update_nonexistent_sample(self):
        """존재하지 않는 샘플 업데이트 시 ValueError"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1']
        })

        new_profile = STRProfile(id='nonexistent', profile={'D3S1358': {'15'}})

        with pytest.raises(ValueError):
            pdm.update_profile_with_STRProfile('nonexistent', new_profile)


class TestInsertNewProfile:
    """insert_new_profile_with_STRProfile() 메서드 테스트"""

    def test_insert_new_profile(self):
        """새 프로파일 삽입"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'D3S1358': ['15-16']
        })

        new_profile = STRProfile(
            id='2023-D-1234-2',
            profile={'D3S1358': {'17', '18'}}
        )

        pdm.insert_new_profile_with_STRProfile('2023-D-1234', '2023-D-1234-2', new_profile)

        assert len(pdm.df_profile) == 2
        assert '2023-D-1234-2' in list(pdm.df_profile['감정물번호'])

    def test_insert_duplicate_sample(self):
        """이미 존재하는 샘플명 삽입 시 ValueError"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'D3S1358': ['15-16']
        })

        new_profile = STRProfile(id='2023-D-1234-1', profile={'D3S1358': {'17'}})

        with pytest.raises(ValueError):
            pdm.insert_new_profile_with_STRProfile('2023-D-1234', '2023-D-1234-1', new_profile)


class TestDeleteProfile:
    """delete_profile_by_samplename() 메서드 테스트"""

    def test_delete_existing_profile(self):
        """존재하는 프로파일 삭제"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1234'],
            '감정물번호': ['2023-D-1234-1', '2023-D-1234-2'],
            'D3S1358': ['15-16', '17-18']
        })

        result = pdm.delete_profile_by_samplename('2023-D-1234-1')

        assert result is True
        assert len(pdm.df_profile) == 1
        assert '2023-D-1234-2' in list(pdm.df_profile['감정물번호'])
        # 인덱스 리셋 확인
        assert list(pdm.df_profile.index) == [0]

    def test_delete_nonexistent_profile(self):
        """존재하지 않는 프로파일 삭제 시 False 반환"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'D3S1358': ['15-16']
        })

        result = pdm.delete_profile_by_samplename('nonexistent')

        assert result is False
        assert len(pdm.df_profile) == 1


class TestCheckInclusion:
    """check_inclusion() 메서드 테스트"""

    def test_inclusion_true(self):
        """포함 관계가 성립하는 경우"""
        pdm = NFSProfileDataManager(kit="STR")
        # STR_20 마커를 위해 필요한 컬럼 추가
        data = {
            '접수번호': ['2023-D-1234', '2023-D-1234'],
            '감정물번호': ['mixed', 'single']
        }
        # 20개 마커 추가
        for marker in pdm.DICT_MARKERS["STR"][:20]:
            if marker == 'D3S1358':
                data[marker] = ['15-16-17', '15-16']
            elif marker == 'vWA':
                data[marker] = ['14-17-18', '14-17']
            else:
                data[marker] = ['', '']

        pdm.df_profile = pd.DataFrame(data)

        result = pdm.check_inclusion('mixed', 'single')
        assert result is True

    def test_inclusion_false(self):
        """포함 관계가 성립하지 않는 경우"""
        pdm = NFSProfileDataManager(kit="STR")
        data = {
            '접수번호': ['2023-D-1234', '2023-D-1234'],
            '감정물번호': ['sample1', 'sample2']
        }
        for marker in pdm.DICT_MARKERS["STR"][:20]:
            if marker == 'D3S1358':
                data[marker] = ['15-16', '17-18']
            else:
                data[marker] = ['', '']

        pdm.df_profile = pd.DataFrame(data)

        result = pdm.check_inclusion('sample1', 'sample2')
        assert result is False


class TestCheckMatch:
    """check_match() 메서드 테스트"""

    def test_match_true(self):
        """일치하는 프로파일"""
        pdm = NFSProfileDataManager(kit="STR")
        data = {
            '접수번호': ['2023-D-1234', '2023-D-1234'],
            '감정물번호': ['sample1', 'sample2']
        }
        for marker in pdm.DICT_MARKERS["STR"][:20]:
            if marker == 'D3S1358':
                data[marker] = ['15-16', '15-16']
            elif marker == 'vWA':
                data[marker] = ['14-17', '14-17']
            else:
                data[marker] = ['', '']

        pdm.df_profile = pd.DataFrame(data)

        result = pdm.check_match('sample1', 'sample2')
        assert result is True

    def test_match_false(self):
        """일치하지 않는 프로파일"""
        pdm = NFSProfileDataManager(kit="STR")
        data = {
            '접수번호': ['2023-D-1234', '2023-D-1234'],
            '감정물번호': ['sample1', 'sample2']
        }
        for marker in pdm.DICT_MARKERS["STR"][:20]:
            if marker == 'D3S1358':
                data[marker] = ['15-16', '17-18']
            else:
                data[marker] = ['', '']

        pdm.df_profile = pd.DataFrame(data)

        result = pdm.check_match('sample1', 'sample2')
        assert result is False


class TestGenerateMixProfile:
    """generate_mix_profile() 메서드 테스트"""

    def test_generate_mix_profile_basic(self):
        """혼합 프로파일 생성"""
        pdm = NFSProfileDataManager(kit="STR")
        data = {
            '접수번호': ['2023-D-1234', '2023-D-1234'],
            '감정물번호': ['sample1', 'sample2']
        }
        for marker in pdm.DICT_MARKERS["STR"]:
            if marker == 'D3S1358':
                data[marker] = ['15-16', '17-18']
            elif marker == 'vWA':
                data[marker] = ['14', '17']
            else:
                data[marker] = ['', '']

        pdm.df_profile = pd.DataFrame(data)

        mixed = pdm.generate_mix_profile(['sample1', 'sample2'])

        assert isinstance(mixed, STRProfile)
        assert mixed.profile['D3S1358'] == {'15', '16', '17', '18'}
        assert mixed.profile['vWA'] == {'14', '17'}

    def test_generate_mix_profile_empty_list(self):
        """빈 리스트로 ValueError 발생"""
        pdm = NFSProfileDataManager(kit="STR")
        with pytest.raises(ValueError):
            pdm.generate_mix_profile([])


class TestFilterByCodecase:
    """filter_by_codecase() 메서드 테스트"""

    def test_filter_existing_case(self):
        """존재하는 사건번호로 필터링"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234', '2023-D-1234', '2023-D-1235'],
            '감정물번호': ['2023-D-1234-1', '2023-D-1234-2', '2023-D-1235-1'],
            'AMEL': ['XY', 'XX', 'XY']
        })

        filtered = pdm.filter_by_codecase('2023-D-1234')

        assert filtered is not None
        assert isinstance(filtered, NFSProfileDataManager)
        assert len(filtered.df_profile) == 2
        assert all(filtered.df_profile['접수번호'] == '2023-D-1234')

    def test_filter_nonexistent_case(self):
        """존재하지 않는 사건번호"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': ['XY']
        })

        filtered = pdm.filter_by_codecase('9999-D-9999')

        # 빈 DataFrame을 가진 PDM 반환
        assert filtered is not None
        assert len(filtered.df_profile) == 0


class TestExtractGenderFromProfile:
    """extract_gender_from_profile() 메서드 테스트"""

    def test_extract_male(self):
        """남성 성별 추출"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': ['XY']
        })

        gender = pdm.extract_gender_from_profile('2023-D-1234-1')
        assert gender == '남성'

    def test_extract_female(self):
        """여성 성별 추출"""
        pdm = NFSProfileDataManager(kit="STR")
        pdm.df_profile = pd.DataFrame({
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1'],
            'AMEL': ['X']
        })

        gender = pdm.extract_gender_from_profile('2023-D-1234-1')
        assert gender == '여성'


class TestExportDfInSet:
    """export_df_in_set() 메서드 테스트"""

    def test_export_basic(self):
        """문자열을 set으로 변환"""
        pdm = NFSProfileDataManager(kit="STR")
        data = {
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1']
        }
        # 모든 마커 컬럼 추가
        for marker in pdm.DICT_MARKERS["STR"]:
            if marker == 'D3S1358':
                data[marker] = ['15-16']
            elif marker == 'vWA':
                data[marker] = ['14']
            else:
                data[marker] = ['']

        pdm.df_profile = pd.DataFrame(data)

        result = pdm.export_df_in_set()

        assert result.loc[0, 'D3S1358'] == {'15', '16'}
        assert result.loc[0, 'vWA'] == {'14'}

    def test_export_empty_allele(self):
        """빈 대립유전자는 빈 set으로"""
        pdm = NFSProfileDataManager(kit="STR")
        data = {
            '접수번호': ['2023-D-1234'],
            '감정물번호': ['2023-D-1234-1']
        }
        # 모든 마커 컬럼을 빈 문자열로 추가
        for marker in pdm.DICT_MARKERS["STR"]:
            data[marker] = ['']

        pdm.df_profile = pd.DataFrame(data)

        result = pdm.export_df_in_set()

        assert result.loc[0, 'AMEL'] == set()
        assert result.loc[0, 'D3S1358'] == set()
