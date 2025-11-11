"""
NFS_STRPROFILE 모듈 테스트
STRProfile 클래스의 기능을 검증합니다.
"""

import pytest
from module.NFS_STRPROFILE import STRProfile


class TestSTRProfileInit:
    """STRProfile 초기화 테스트"""

    def test_empty_profile_creation(self):
        """빈 프로파일 생성 테스트"""
        profile = STRProfile()
        assert profile.id == ""
        assert profile.profile == {}

    def test_profile_with_id_only(self):
        """ID만 있는 프로파일 생성"""
        profile = STRProfile(id="Sample001")
        assert profile.id == "Sample001"
        assert profile.profile == {}

    def test_profile_with_data(self):
        """ID와 프로파일 데이터로 생성"""
        test_data = {
            "D3S1358": {"15", "16"},
            "vWA": {"14", "17"}
        }
        profile = STRProfile(id="Sample001", profile=test_data)
        assert profile.id == "Sample001"
        assert profile.profile == test_data

    def test_profile_none_handling(self):
        """profile=None 처리 확인"""
        profile = STRProfile(id="Test", profile=None)
        assert profile.profile == {}


class TestCheckMatch:
    """check_match() 메서드 테스트"""

    def test_identical_profiles(self):
        """완전히 일치하는 프로파일 비교"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}, "vWA": {"14", "17"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"15", "16"}, "vWA": {"14", "17"}})
        assert profile1.check_match(profile2) is True

    def test_different_profiles(self):
        """일치하지 않는 프로파일 비교"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"15", "17"}})
        assert profile1.check_match(profile2) is False

    def test_no_common_loci(self):
        """공통 좌위가 없는 경우"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"vWA": {"14", "17"}})
        # 공통 좌위가 없으면 True 반환 (모든 공통 좌위에서 일치)
        assert profile1.check_match(profile2) is True

    def test_partial_overlap(self):
        """일부 좌위만 공통인 경우"""
        profile1 = STRProfile(id="A", profile={
            "D3S1358": {"15", "16"},
            "vWA": {"14", "17"}
        })
        profile2 = STRProfile(id="B", profile={
            "D3S1358": {"15", "16"},
            "FGA": {"21", "24"}
        })
        assert profile1.check_match(profile2) is True

    def test_type_error(self):
        """잘못된 타입 입력 시 TypeError 발생"""
        profile = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        with pytest.raises(TypeError):
            profile.check_match("not a profile")


class TestCheckInclusion:
    """check_inclusion() 메서드 테스트"""

    def test_mixed_includes_single(self):
        """혼합 프로파일이 단일 프로파일을 포함"""
        mixed = STRProfile(id="Mixed", profile={"D3S1358": {"15", "16", "17"}})
        single = STRProfile(id="Single", profile={"D3S1358": {"15", "16"}})
        assert mixed.check_inclusion(single) is True

    def test_single_not_include_mixed(self):
        """단일 프로파일이 혼합 프로파일을 포함하지 않음"""
        single = STRProfile(id="Single", profile={"D3S1358": {"15", "16"}})
        mixed = STRProfile(id="Mixed", profile={"D3S1358": {"15", "16", "17"}})
        assert single.check_inclusion(mixed) is False

    def test_partial_inclusion(self):
        """부분 포함 케이스"""
        profile1 = STRProfile(id="A", profile={
            "D3S1358": {"15", "16", "17"},
            "vWA": {"14"}
        })
        profile2 = STRProfile(id="B", profile={
            "D3S1358": {"15", "16"},
            "vWA": {"14", "17"}
        })
        # D3S1358는 포함하지만 vWA는 포함하지 않음
        assert profile1.check_inclusion(profile2) is False

    def test_identical_profiles_inclusion(self):
        """동일한 프로파일은 포함 관계"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"15", "16"}})
        assert profile1.check_inclusion(profile2) is True

    def test_inclusion_type_error(self):
        """잘못된 타입 입력 시 TypeError 발생"""
        profile = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        with pytest.raises(TypeError):
            profile.check_inclusion("not a profile")


class TestUnionProfiles:
    """union_profiles() 메서드 테스트"""

    def test_union_basic(self):
        """기본 합집합 생성"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"17", "18"}})
        mixed = profile1.union_profiles(profile2)

        assert mixed.id == "A + B"
        assert mixed.profile["D3S1358"] == {"15", "16", "17", "18"}

    def test_union_with_overlap(self):
        """중복된 대립유전자가 있는 경우"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={"D3S1358": {"16", "17"}})
        mixed = profile1.union_profiles(profile2)

        assert mixed.profile["D3S1358"] == {"15", "16", "17"}

    def test_union_multiple_loci(self):
        """여러 좌위에서 합집합"""
        profile1 = STRProfile(id="A", profile={
            "D3S1358": {"15", "16"},
            "vWA": {"14"}
        })
        profile2 = STRProfile(id="B", profile={
            "D3S1358": {"17"},
            "vWA": {"14", "17"}
        })
        mixed = profile1.union_profiles(profile2)

        assert mixed.profile["D3S1358"] == {"15", "16", "17"}
        assert mixed.profile["vWA"] == {"14", "17"}

    def test_union_with_empty_profile(self):
        """빈 프로파일과 합집합"""
        profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        profile2 = STRProfile(id="B", profile={})
        mixed = profile1.union_profiles(profile2)

        assert mixed.id == "A + B"
        assert mixed.profile == {}  # 공통 좌위가 없으므로 빈 딕셔너리

    def test_union_type_error(self):
        """잘못된 타입 입력 시 TypeError 발생"""
        profile = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
        with pytest.raises(TypeError):
            profile.union_profiles("not a profile")


class TestExportToStr:
    """export_to_str() 메서드 테스트"""

    def test_numeric_alleles_sorting(self):
        """숫자 대립유전자 정렬 (수치순)"""
        profile = STRProfile(id="Test", profile={"D3S1358": {"16", "15", "18"}})
        result = profile.export_to_str()
        assert result["D3S1358"] == "15-16-18"

    def test_string_alleles_sorting(self):
        """문자 대립유전자 정렬 (알파벳순)"""
        profile = STRProfile(id="Test", profile={"AMEL": {"Y", "X"}})
        result = profile.export_to_str()
        assert result["AMEL"] == "X-Y"

    def test_mixed_alleles_sorting(self):
        """숫자와 문자 혼합 대립유전자"""
        profile = STRProfile(id="Test", profile={
            "D3S1358": {"16", "15"},
            "AMEL": {"X", "Y"}
        })
        result = profile.export_to_str()
        assert result["D3S1358"] == "15-16"
        assert result["AMEL"] == "X-Y"

    def test_decimal_alleles_sorting(self):
        """소수점 포함 대립유전자 정렬"""
        profile = STRProfile(id="Test", profile={"TH01": {"9.3", "10", "9"}})
        result = profile.export_to_str()
        assert result["TH01"] == "9-9.3-10"

    def test_single_allele(self):
        """단일 대립유전자"""
        profile = STRProfile(id="Test", profile={"D3S1358": {"15"}})
        result = profile.export_to_str()
        assert result["D3S1358"] == "15"

    def test_empty_profile(self):
        """빈 프로파일"""
        profile = STRProfile(id="Test", profile={})
        result = profile.export_to_str()
        assert result == {}


class TestStringRepresentation:
    """__str__과 __repr__ 메서드 테스트"""

    def test_str_representation(self):
        """__str__ 메서드 테스트"""
        profile = STRProfile(id="Sample001", profile={
            "D3S1358": {"15", "16"},
            "vWA": {"14", "17"}
        })
        result = str(profile)
        assert "Sample001" in result
        assert "loci_count=2" in result

    def test_repr_representation(self):
        """__repr__ 메서드 테스트"""
        profile = STRProfile(id="Sample001", profile={"D3S1358": {"15", "16"}})
        result = repr(profile)
        assert "STRProfile" in result
        assert "Sample001" in result
        assert "D3S1358" in result
