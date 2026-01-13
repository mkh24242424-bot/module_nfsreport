import logging
import pandas as pd
import re
import os
from . import dataframe as NFS_DF
from . import strprofile as NFS_SP
from .exceptions import EvidenceNotFoundError
from .constants_strprofile import DICT_MARKERS
from .likelihood_calculator import LikelihoodCalculator
from typing import Self, Optional, Literal

logger = logging.getLogger(__name__)

class NFSProfileDataManager:
    """STR/Y-STR 유전자 프로필 데이터 관리 및 분석

    국립과학수사연구원(NFS)의 DNA 감정서 생성 시스템에서 사용하는
    STR 및 Y-STR 프로필 데이터를 관리하고 분석하는 클래스입니다.

    주요 기능:
        - Tomato 소프트웨어 출력 파일 로딩 및 전처리
        - 프로필 데이터 필터링, 병합, 삭제
        - 프로필 간 일치/포함 관계 분석
        - 개인식별지수 계산
        - 혼합 프로필 생성

    Attributes:
        df_profile: 프로필 데이터를 저장하는 DataFrame
        kit: 사용 중인 키트 타입 ("STR" 또는 "YSTR")
        likelihood_calculator: 개인식별지수 계산을 위한 LikelihoodCalculator 인스턴스

    Note:
        DICT_MARKERS, PROB_NOMATCH, TA_THRESHOLD 등의 상수는
        constants_strprofile 모듈에서 정의됩니다

    Examples:
        >>> # STR 프로필 매니저 생성 및 데이터 로딩
        >>> pdm = NFSProfileDataManager(kit="STR")
        >>> pdm.load_combined_result_from_tomato("tomato_result.xlsx")
        >>>
        >>> # 특정 케이스 필터링
        >>> case_pdm = pdm.filter_by_codecase("2025-C-1234")
        >>>
        >>> # 프로필 일치 확인
        >>> is_match = pdm.check_match("sample1", "sample2")
        >>>
        >>> # 개인식별지수 계산
        >>> lr = pdm.calculate_likelihood_from_profile("evidence1")

    See Also:
        STRProfile: 개별 프로필 객체
        LikelihoodCalculator: 개인식별지수 계산기
    """

    # 인스턴스 변수 타입 힌트
    df_profile: pd.DataFrame
    kit: Literal["STR", "YSTR"]
    likelihood_calculator: LikelihoodCalculator

    # ==================== Initialization ====================

    def __init__(
        self,
        kit: Literal["STR", "YSTR"] = "STR",
        likelihood_calculator: Optional[LikelihoodCalculator] = None,
    ):
        """NFSProfileDataManager 초기화

        지정된 키트 타입(STR 또는 YSTR)으로 프로필 데이터 매니저를 생성합니다.
        빈 DataFrame과 LikelihoodCalculator를 초기화합니다.

        Args:
            kit: 사용할 키트 타입. 기본값은 "STR"
            likelihood_calculator: 개인식별지수 계산기. None이면 기본 계산기 사용

        Raises:
            ValueError: kit이 "STR" 또는 "YSTR"이 아닌 경우

        Examples:
            >>> # 기본 계산기 사용
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> pdm.kit
            'STR'
            >>>
            >>> # 커스텀 계산기 주입
            >>> custom_calc = LikelihoodCalculator()
            >>> pdm = NFSProfileDataManager(kit="STR", likelihood_calculator=custom_calc)
        """
        logger.info(f"NFSProfileDataManager 초기화 시작 (kit={kit})")

        # kit 값 검증
        if kit not in ("STR", "YSTR"):
            logger.error(f"지원되지 않는 kit 타입: {kit}")
            raise ValueError(f"kit은 'STR' 또는 'YSTR'이어야 합니다. 입력값: {kit}")

        # 프로필 데이터를 저장할 DataFrame 초기화
        self.df_profile = pd.DataFrame()
        self.kit = kit

        # 우도비 계산기 초기화 (주입된 계산기 또는 기본 계산기)
        self.likelihood_calculator = likelihood_calculator or LikelihoodCalculator()

        logger.info(f"NFSProfileDataManager 초기화 완료 (kit={kit})")

    # ==================== Data Loading ====================

    def load_combined_result_from_tomato(self, path: str) -> None:
        """Tomato 엑셀 파일에서 CombinedResult 시트를 로드하여 가공

        데이터 로딩 파이프라인:
        1. 파일 존재 확인
        2. Excel 파일 읽기 (CombinedResult 시트)
        3. 상태 분석 (_analyze_status_combined)
        4. 전처리 (_preprocess_tomato_dataframe)
        5. df_profile에 저장

        Args:
            path: 읽어올 토마토 파일 경로 (절대/상대 경로 모두 가능)

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            ValueError: CombinedResult 시트가 없는 경우

        See Also:
            _analyze_status_combined: 프로필 상태 분석 헬퍼 메서드
            _preprocess_tomato_dataframe: 데이터 전처리 헬퍼 메서드
        """
        logger.info(f"Tomato 파일 로딩 시작: {path}")

        # 1. 파일 존재 확인
        if not os.path.exists(path):
            logger.error(f"파일을 찾을 수 없음: {path}")
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {path}")

        # 2. Excel 파일 읽기
        try:
            df_tomato = pd.read_excel(path, sheet_name="CombinedResult", header=1)
        except ValueError as e:
            logger.error(f"CombinedResult 시트를 찾을 수 없음: {path}")
            raise ValueError(f"'CombinedResult' 시트가 존재하지 않습니다: {path}") from e

        if df_tomato.empty:
            logger.warning(f"빈 데이터프레임 로드됨: {path}")

        logger.debug(f"엑셀 파일 읽기 완료 (rows={len(df_tomato)})")

        # 3. 상태 분석
        df_analyzed = self._analyze_status_combined(df_tomato)
        logger.debug(f"상태 분석 완료")

        # 4. 전처리
        df_processed = self._preprocess_tomato_dataframe(df_analyzed)
        logger.debug(f"전처리 완료")

        # 5. 결과 저장
        self.df_profile = df_processed
        logger.info(f"Tomato 파일 로딩 완료 (최종 프로필 수={len(self.df_profile)})")

    def _analyze_status_combined(self, df: pd.DataFrame) -> pd.DataFrame:
        """프로필 데이터가 합쳐진 상태를 분석해서 정리

        load_combined_result_from_tomato()에서 사용되는 헬퍼 메서드.
        Tomato 소프트웨어에서 생성한 CombinedResult의 프로필 상태를 분류합니다.

        분류 기준:
        - UNIQUE: 한 번만 실험한 데이터
        - CROSSCHECKED: 여러 번 실험하여 통합된 데이터 (Sample ID가 공란)
        - DUPLICATED: 추정형 분석을 위해 복사된 데이터

        Args:
            df: 분석할 토마토 데이터프레임

        Returns:
            pd.DataFrame: STATUS_COMBINED 컬럼이 추가된 데이터프레임

        Raises:
            ValueError: 필수 컬럼이 누락된 경우
        """
        logger.debug(f"프로필 상태 분석 시작 (총 {len(df)} 행)")

        # 필수 컬럼 확인
        required_cols = ["Sample Name", "Sample ID"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"필수 컬럼 누락: {missing_cols}")
            raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_cols}")

        df_analyzed = df.copy()
        df_analyzed["STATUS_COMBINED"] = "DEFAULT"

        # 1. UNIQUE: 한 번만 실험한 데이터
        unique_mask = ~df_analyzed["Sample Name"].duplicated(keep=False)
        df_analyzed.loc[unique_mask, "STATUS_COMBINED"] = "UNIQUE"

        # 2. CROSSCHECKED: 여러 번 실험한 데이터가 합쳐진 결과 (Tomato가 자동으로 통합)
        crosschecked_mask = df_analyzed["Sample ID"].isna()
        df_analyzed.loc[crosschecked_mask, "STATUS_COMBINED"] = "CROSSCHECKED"

        # 3. DUPLICATED: 추정형을 위해 Tomato가 복사한 데이터
        duplicated_mask = df_analyzed["Sample ID"] == "Duplicated data of above line"
        df_analyzed.loc[duplicated_mask, "STATUS_COMBINED"] = "DUPLICATED"

        # 복사된 데이터는 Sample Name에 '+'를 추가해 별개의 프로필로 취급
        df_analyzed.loc[duplicated_mask, "Sample Name"] = str(df_analyzed.loc[duplicated_mask, "Sample Name"]) + "+"
        

        # 분류 결과 통계
        status_counts = df_analyzed["STATUS_COMBINED"].value_counts().to_dict()
        logger.debug(f"상태 분류 완료: {status_counts}")

        # DEFAULT 상태 경고 (예상치 못한 케이스)
        default_count = status_counts.get("DEFAULT", 0)
        if default_count > 0:
            logger.warning(
                f"분류되지 않은 DEFAULT 상태 {default_count}건 발견. "
                f"데이터 확인 필요"
            )

        return df_analyzed

    def _preprocess_tomato_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """토마토 데이터프레임 전처리

        load_combined_result_from_tomato()에서 사용되는 헬퍼 메서드.

        전처리 단계:
        1. 사건번호 형식 검증 및 필터링 (예: 2023-D-1234)
        2. 컬럼명 한글로 변경
        3. 필요한 컬럼만 추출 (접수번호, 감정물번호, STATUS_COMBINED, 마커들)
        4. DEFAULT 상태 제거
        5. 결측값 처리 및 정렬

        Args:
            df: 토마토 데이터프레임

        Returns:
            pd.DataFrame: 전처리가 완료된 토마토 데이터프레임

        Raises:
            ValueError: 필수 컬럼이 누락된 경우
        """
        logger.debug(f"토마토 데이터 전처리 시작 (총 {len(df)} 행)")

        # 필수 컬럼 확인
        required_cols = ["Case Number", "Sample Name", "STATUS_COMBINED", "Amelogenin"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"필수 컬럼 누락: {missing_cols}")
            raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_cols}")

        df_preprocessed = df.copy()

        # 1. 사건번호 형식 검증: YYYY-X-NNNN (예: 2023-D-1234)
        case_number_pattern = re.compile(r"\d+[-]\w[-]\d+")
        is_valid_case_number = df_preprocessed["Sample Name"].str.match(
            case_number_pattern, na=False
        )
        df_preprocessed = df_preprocessed[is_valid_case_number]
        logger.debug(f"사건번호 필터링 완료: {len(df)} → {len(df_preprocessed)} 행")

        if df_preprocessed.empty:
            logger.warning("사건번호 필터링 후 데이터가 비어있습니다")
            return pd.DataFrame()

        # 2. 컬럼명 한글로 변경
        df_preprocessed = df_preprocessed.rename(
            columns={
                "Case Number": "접수번호",
                "Sample Name": "감정물번호",
                "Amelogenin": "AMEL",
            }
        )

        # 3. 필요한 컬럼만 추출
        selected_columns = ["접수번호", "감정물번호", "STATUS_COMBINED"] + DICT_MARKERS[self.kit]
        df_preprocessed = df_preprocessed[selected_columns]

        # 4. DEFAULT 상태 제거 (분류되지 않은 데이터)
        before_count = len(df_preprocessed)
        df_preprocessed = df_preprocessed.loc[df_preprocessed["STATUS_COMBINED"] != "DEFAULT"]
        after_count = len(df_preprocessed)

        if before_count > after_count:
            logger.debug(f"DEFAULT 상태 제거: {before_count} → {after_count} 행")

        # 5. 결측값 처리 및 정렬
        df_preprocessed = df_preprocessed.fillna("")
        df_preprocessed = NFS_DF.sort_by_serial_number(df_preprocessed, key_column="감정물번호")

        logger.debug(f"전처리 완료 (최종 {len(df_preprocessed)} 행)")
        return df_preprocessed

    # ==================== Data Export ====================

    def export_df_in_set(self, STR_20: bool = False) -> pd.DataFrame:
        """알릴 문자열을 set으로 변환한 데이터프레임 반환

        각 마커의 알릴 문자열을 Python set으로 변환합니다.
        STR-20 모드 지원: STR 키트에서 20개 마커만 사용 가능.

        Args:
            STR_20: True일 경우 STR-20 마커만 사용. 기본값은 False

        Returns:
            pd.DataFrame: 알릴 데이터가 set으로 변환된 데이터프레임

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> df = pdm.export_df_in_set(STR_20=True)
            >>> # 변환 형식: "15-16" → {"15", "16"}, "12" → {"12"}, "" → set()
        """
        logger.debug(f"프로필 데이터 변환 시작 (STR_20={STR_20}, kit={self.kit})")

        if self.df_profile.empty:
            logger.warning("빈 데이터프레임입니다. 빈 DataFrame 반환")
            return pd.DataFrame()

        df_profile = self.df_profile.copy()

        # STR 키트에서 STR_20이 True이면 STR20 마커 사용
        marker_key = "STR20" if (STR_20 and self.kit == "STR") else self.kit
        list_markers = DICT_MARKERS[marker_key]

        # 각 마커의 알릴 문자열을 set으로 변환: "15-16" → {"15", "16"}
        for marker in list_markers:
            df_profile[marker] = df_profile[marker].apply(
                lambda x: set(str(x).split("-")) if x != "" else set()
            )

        logger.debug(f"프로필 데이터 변환 완료 (마커 수={len(list_markers)})")
        return df_profile

    # ==================== Data Management ====================

    def concatenate(self, new_NPDM: "NFSProfileDataManager") -> None:
        """새로운 ProfileDataManager의 데이터를 현재 객체에 병합

        병합 파이프라인:
        1. 호환성 검사 (_validate_compatibility)
        2. 데이터 병합 및 대립유전자 개수 계산 (_count_allele)
        3. 중복 데이터 탐지 및 해결 (_resolve_duplicate_profile)
        4. 정리 및 정렬

        중복 해결 우선순위:
        - CROSSCHECKED vs CROSSCHECKED: 대립유전자 개수가 많은 것 선택
        - CROSSCHECKED vs UNIQUE: CROSSCHECKED 선택
        - 기타: 새 데이터 선택

        Args:
            new_NPDM: 병합할 NFSProfileDataManager 객체

        See Also:
            _validate_compatibility: 호환성 검사 헬퍼 메서드
            _count_allele: 대립유전자 개수 계산 헬퍼 메서드
            _resolve_duplicate_profile: 중복 프로필 해결 헬퍼 메서드
        """
        logger.info(f"프로필 병합 시작 (기존={len(self.df_profile)}, 추가={len(new_NPDM.df_profile)})")

        # 1. 호환성 검사
        if not self._validate_compatibility(new_NPDM):
            logger.warning("병합 실패: 호환성 검사 실패")
            return  # Early return

        # 2. 데이터 병합 및 대립유전자 개수 계산
        concat_profile = pd.concat(
            [self.df_profile, new_NPDM.df_profile], axis=0
        ).reset_index(drop=True)
        concat_profile["CNT_ALLELE"] = concat_profile.apply(self._count_allele, axis=1)

        # 3. 중복 데이터 탐지 및 해결
        duplicated_sample_names = concat_profile.loc[
            concat_profile.duplicated(subset="감정물번호", keep=False), "감정물번호"
        ].unique()

        if len(duplicated_sample_names) > 0:
            logger.debug(f"중복 샘플 감지: {len(duplicated_sample_names)}개")

        list_drop_idx = []
        for sample_name in duplicated_sample_names:
            data_old = concat_profile[concat_profile["감정물번호"] == sample_name].iloc[0]
            data_new = concat_profile[concat_profile["감정물번호"] == sample_name].iloc[1]
            idx_to_drop = self._resolve_duplicate_profile(data_old, data_new)
            list_drop_idx.append(idx_to_drop)

        # 4. 정리 및 정렬
        df_cleaned = concat_profile.drop(index=list_drop_idx, axis=0).reset_index(drop=True)
        df_cleaned = df_cleaned.drop("CNT_ALLELE", axis=1)
        self.df_profile = NFS_DF.sort_by_serial_number(df_cleaned, key_column="감정물번호")

        logger.info(f"프로필 병합 완료 (최종={len(self.df_profile)}, 중복 제거={len(list_drop_idx)})")

    def _validate_compatibility(self, new_NPDM: "NFSProfileDataManager") -> bool:
        """두 ProfileDataManager의 병합 호환성 검사

        concatenate()에서 사용되는 헬퍼 메서드.
        키트 타입과 컬럼 구조가 동일한지 확인합니다.

        Args:
            new_NPDM: 병합하려는 NFSProfileDataManager 객체

        Returns:
            bool: 호환 가능하면 True, 불가능하면 False
        """
        # 키트 타입 확인
        if self.kit != new_NPDM.kit:
            logger.warning(f"키트 타입 불일치 (기존={self.kit}, 신규={new_NPDM.kit})")
            return False

        # 컬럼 구조 확인 (양방향 차이 검사)
        column_differences = set(self.df_profile.columns).symmetric_difference(
            set(new_NPDM.df_profile.columns)
        )
        if len(column_differences) > 0:
            logger.warning(
                f"컬럼 구조 불일치 (차이={column_differences}). "
                f"두 데이터프레임의 컬럼이 완전히 일치해야 합니다."
            )
            return False

        return True

    def _count_allele(self, row: pd.Series) -> int:
        """프로필 행에서 대립유전자가 존재하는 마커 개수 계산

        concatenate()에서 사용되는 헬퍼 메서드.
        중복 프로필 해결 시 더 완전한 프로필을 선택하기 위해 사용됩니다.

        Args:
            row: 프로필 DataFrame의 한 행 (Series)

        Returns:
            int: 데이터가 있는 마커 개수
        """
        allele_count = 0
        for marker in DICT_MARKERS[self.kit]:
            if not pd.isna(row[marker]):
                allele_count += 1
        return allele_count

    def _resolve_duplicate_profile(self, data_old: pd.Series, data_new: pd.Series) -> object:
        """중복된 프로필 중 제거할 프로필의 인덱스 결정

        concatenate()에서 사용되는 헬퍼 메서드.

        우선순위 규칙:
        1. CROSSCHECKED vs CROSSCHECKED: 대립유전자 개수가 많은 것 유지
        2. CROSSCHECKED vs UNIQUE: CROSSCHECKED 유지 (순서 무관)
        3. 기타: 새 데이터 유지 (기존 데이터 제거)

        Args:
            data_old: 기존 프로필 데이터 (Series)
            data_new: 새 프로필 데이터 (Series)

        Returns:
            int: 제거할 프로필의 DataFrame 인덱스
        """
        sample_name = data_old["감정물번호"]  # 중복이므로 두 데이터 모두 같은 감정물번호
        status_old = data_old["STATUS_COMBINED"]
        status_new = data_new["STATUS_COMBINED"]

        # 1. 둘 다 CROSSCHECKED: 대립유전자 개수로 결정
        if status_old == "CROSSCHECKED" and status_new == "CROSSCHECKED":
            if data_old["CNT_ALLELE"] > data_new["CNT_ALLELE"]:
                logger.debug(f"중복 해결: {sample_name} - 기존 유지 (더 많은 대립유전자)")
                return data_new.name
            else:
                logger.debug(f"중복 해결: {sample_name} - 신규 유지 (더 많은 대립유전자)")
                return data_old.name

        # 2a. CROSSCHECKED vs UNIQUE: CROSSCHECKED 우선
        elif status_old == "CROSSCHECKED" and status_new == "UNIQUE":
            logger.debug(f"중복 해결: {sample_name} - 기존 유지 (CROSSCHECKED 우선)")
            return data_new.name

        # 2b. UNIQUE vs CROSSCHECKED: CROSSCHECKED 우선
        elif status_old == "UNIQUE" and status_new == "CROSSCHECKED":
            logger.debug(f"중복 해결: {sample_name} - 신규 유지 (CROSSCHECKED 우선)")
            return data_old.name

        # 3. 기타: 새 데이터 우선
        else:
            logger.debug(f"중복 해결: {sample_name} - 신규 유지 (기본 규칙)")
            return data_old.name

    def filter_by_codecase(self, code_case: str) -> Optional[Self]:
        """접수번호로 프로필 데이터를 필터링하여 새로운 ProfileDataManager 반환

        Args:
            code_case: 필터링할 접수번호 (예: "2025-C-6845")

        Returns:
            Optional[Self]: 필터링된 프로필을 포함한 새 NFSProfileDataManager 객체.
                            해당 접수번호가 없으면 빈 프로필을 가진 객체 반환.

        Raises:
            EvidenceNotFoundError: '접수번호' 컬럼이 존재하지 않을 경우

        Examples:
            >>> pdm_filtered = pdm.filter_by_codecase("2025-C-6845")
            >>> print(len(pdm_filtered.df_profile))
            5
        """
        logger.debug(f"접수번호로 필터링 시작 (code_case={code_case})")

        try:
            # 접수번호로 필터링
            df_filtered = self.df_profile.loc[
                self.df_profile['접수번호'] == code_case, :
            ].reset_index(drop=True)

            if df_filtered.empty:
                logger.warning(f"접수번호 '{code_case}'에 해당하는 프로필이 없습니다")

            logger.debug(f"필터링 완료 (code_case={code_case}, 프로필 수={len(df_filtered)})")
            return self._get_instance(kit=self.kit, df_profile=df_filtered)
        except KeyError as e:
            logger.error(f"{code_case}의 증거물 정보 필터링 실패: 필수 컬럼 누락 (원인: {e})")
            raise EvidenceNotFoundError(code_case, f"증거물 정보 필터링 실패: 필수 컬럼 누락 - {e}") from e


    @classmethod
    def _get_instance(cls, kit: Literal["STR", "YSTR"], df_profile: pd.DataFrame) -> Self:
        """주어진 프로필 데이터로 새로운 NFSProfileDataManager 인스턴스 생성

        filter_by_codecase()에서 사용되는 헬퍼 메서드.
        Factory pattern으로 동작하여 기존 인스턴스의 설정을 유지하면서
        필터링된 데이터를 가진 새 인스턴스를 생성합니다.

        Args:
            kit: 사용할 키트 타입 ("STR" 또는 "YSTR")
            df_profile: 새 인스턴스에 설정할 프로필 DataFrame

        Returns:
            Self: 설정된 프로필 데이터를 가진 새 NFSProfileDataManager 인스턴스

        Examples:
            >>> new_pdm = NFSProfileDataManager._get_instance(
            ...     kit="STR", df_profile=filtered_df
            ... )
        """
        instance = cls(kit=kit)
        instance.df_profile = df_profile.copy()
        return instance

    def length(self) -> int:
        """프로필 데이터의 개수 반환

        Returns:
            int: df_profile의 행 개수 (프로필 개수)

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> pdm.length()
            10
        """
        return self.df_profile.shape[0]

    # ==================== Profile Analysis ====================

    def extract_gender_from_profile(self, code_evidence: str) -> str:
        """감정물번호에 해당하는 프로필의 성별 반환

        Amelogenin(AMEL) 마커를 사용하여 성별을 판단합니다.
        - AMEL = "X": 여성
        - AMEL = "XY" 또는 기타: 남성

        Args:
            code_evidence: 감정물번호 (예: "2025-C-6845-1")

        Returns:
            str: "여성" 또는 "남성"

        Raises:
            ValueError: 해당 감정물번호의 프로필을 찾을 수 없는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> gender = pdm.extract_gender_from_profile("2025-C-6845-1")
            >>> print(gender)
            여성
        """
        logger.debug(f"성별 추출 시작 (code_evidence={code_evidence})")

        # 프로필 검색
        profile_mask = self.df_profile["감정물번호"] == code_evidence
        matching_profiles = self.df_profile[profile_mask]

        if matching_profiles.empty:
            logger.error(f"프로필을 찾을 수 없음 (code_evidence={code_evidence})")
            raise ValueError(f"감정물번호 '{code_evidence}'에 해당하는 프로필을 찾을 수 없습니다.")

        # AMEL 마커로 성별 판단
        amel_value = matching_profiles.iloc[0]["AMEL"]
        gender = "여성" if amel_value == "X" else "남성"

        logger.debug(f"성별 추출 완료 (code_evidence={code_evidence}, AMEL={amel_value}, gender={gender})")
        return gender

    def calculate_likelihood_from_profile(self, code_evidence: str) -> tuple:
        """감정물 번호에 해당하는 프로필의 개인식별지수 계산

        STR-20 마커만 사용하여 프로필을 생성하고,
        LikelihoodCalculator로 개인식별지수를 계산합니다.

        Args:
            code_evidence: 감정물번호

        Returns:
            tuple: 감정서 폼으로 쓰여진 개인식별지수 (계수, 지수)
                   e.g., ("4.0", "10") = 4.0 x 10^10

        Examples:
            >>> pm = NFSProfileDataManager(kit="STR")
            >>> pm.load_combined_result_from_tomato("tomato.xlsx")
            >>> coefficient, exponent = pm.calculate_likelihood_from_profile("A-1")
            >>> print(f"{coefficient} x 10^{exponent}")
            4.0 x 10^10
        """
        logger.debug(f"개인식별지수 계산 시작 (code_evidence={code_evidence})")

        # STR-20 마커만 포함된 프로필 생성
        str_profile = self.generate_STRProfile(code_evidence, STR_20=True)

        # LikelihoodCalculator로 계산
        result = self.likelihood_calculator.calculate(str_profile)

        logger.debug(
            f"개인식별지수 계산 완료 (code_evidence={code_evidence}, "
            f"LR={result[0]}x10^{result[1]})"
        )
        return result

    def check_inclusion(self, target_samplename: str, query_samplename: str) -> bool:
        """타겟 샘플이 쿼리 샘플을 포함하는지 확인

        두 샘플의 STR 프로필을 생성하고, 타겟 프로필이 쿼리 프로필의
        모든 알릴을 포함하는지 검사합니다. (STR-20 마커 사용)

        Args:
            target_samplename: 포함 여부를 확인할 대상 샘플명
            query_samplename: 포함되는지 확인할 쿼리 샘플명

        Returns:
            bool: 타겟이 쿼리를 포함하면 True, 그렇지 않으면 False

        Raises:
            ValueError: 샘플명을 찾을 수 없는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> pdm.check_inclusion("mixed_sample", "contributor1")
            True
            >>> pdm.check_inclusion("single_sample", "different_sample")
            False
        """
        logger.debug(f"포함 확인 시작 (target={target_samplename}, query={query_samplename})")

        # STR 프로필 생성 (20개 마커 사용)
        target_profile = self.generate_STRProfile(target_samplename, STR_20=True)
        query_profile = self.generate_STRProfile(query_samplename, STR_20=True)

        # 포함 관계 확인
        result = target_profile.check_inclusion(query_profile)

        logger.info(f"포함 확인 완료 (target={target_samplename}, query={query_samplename}, result={result})")
        return result

    def check_match(self, target_samplename: str, query_samplename: str) -> bool:
        """두 샘플의 STR 프로필이 일치하는지 확인

        두 샘플의 STR 프로필을 생성하고, 모든 로커스에서
        알릴이 정확히 일치하는지 검사합니다. (STR-20 마커 사용)

        Args:
            target_samplename: 비교할 첫 번째 샘플명
            query_samplename: 비교할 두 번째 샘플명

        Returns:
            bool: 두 프로필이 일치하면 True, 그렇지 않으면 False

        Raises:
            ValueError: 샘플명을 찾을 수 없는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> pdm.check_match("sample1", "sample2")
            False
            >>> pdm.check_match("sample1", "sample1_duplicate")
            True
        """
        logger.debug(f"일치 확인 시작 (target={target_samplename}, query={query_samplename})")

        # STR 프로필 생성 (20개 마커 사용)
        target_profile = self.generate_STRProfile(target_samplename, STR_20=True)
        query_profile = self.generate_STRProfile(query_samplename, STR_20=True)

        # 일치 여부 확인
        result = target_profile.check_match(query_profile)

        logger.info(f"일치 확인 완료 (target={target_samplename}, query={query_samplename}, result={result})")
        return result

    # ==================== STRProfile Operations ====================

    def generate_STRProfile(
        self, samplename: str, STR_20: bool = False
    ) -> NFS_SP.STRProfile:
        """샘플명과 키트 정보를 바탕으로 STR 프로파일 객체를 생성

        Args:
            samplename: 감정물 번호/샘플 이름
            STR_20: 20개 마커 사용 여부. 기본값은 False

        Returns:
            STRProfile: 생성된 STR 프로파일 객체

        Raises:
            ValueError: 샘플명이 데이터에서 찾을 수 없는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> profile = pdm.generate_STRProfile("S001", STR_20=True)
            >>> print(profile.id)
            S001
        """
        logger.debug(f"STRProfile 생성 시작 (samplename={samplename}, STR_20={STR_20})")
        # 마커 리스트 결정: STR 키트에서 STR_20이 True이면 STR20 마커 사용
        marker_key = "STR20" if (STR_20 and self.kit == "STR") else self.kit
        list_markers = DICT_MARKERS[marker_key]

        # 샘플 데이터 조회 (예외 처리 추가)
        sample_data = self.df_profile[self.df_profile["감정물번호"] == samplename]
        if sample_data.empty:
            logger.error(f"ValueError: 샘플 '{samplename}'을 찾을 수 없습니다.")
            raise ValueError(f"샘플 '{samplename}'을 찾을 수 없습니다.")

        dict_profile = sample_data.fillna("").iloc[0].to_dict()

        # 프로파일 딕셔너리 생성
        dict_profile_set = {}
        for marker in list_markers:
            value = str(dict_profile.get(marker, ""))
            if value:  # 더 pythonic한 빈 문자열 체크
                dict_profile_set[marker] = set(value.split("-"))

        logger.debug(f"STRProfile 생성 완료 (samplename={samplename}, 좌위 수={len(dict_profile_set)})")
        return NFS_SP.STRProfile(id=samplename, profile=dict_profile_set)

    def generate_empty_STRProfile(self, samplename: str = "") -> NFS_SP.STRProfile:
        """지정된 키트의 모든 마커에 대해 빈 값을 가진 STR 프로파일 객체를 생성

        주로 혼합 프로필을 생성할 때 시작 프로파일로 사용됩니다.
        모든 마커 위치에 빈 set()이 할당되어 있어 나중에 데이터를 추가할 수 있습니다.

        Args:
            samplename: 생성할 프로필의 id. 기본값은 빈 문자열

        Returns:
            STRProfile: 모든 마커가 빈 set으로 초기화된 STR 프로파일 객체

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> empty_profile = pdm.generate_empty_STRProfile("MIXED-001")
            >>> len(empty_profile.profile)
            24
        """
        logger.debug(f"빈 STRProfile 생성 시작 (samplename={samplename}, kit={self.kit})")

        # 키트에 해당하는 마커 리스트 조회
        list_markers = DICT_MARKERS[self.kit]

        # 모든 마커에 대해 빈 set으로 초기화된 프로파일 딕셔너리 생성
        dict_profile_set = {marker: set() for marker in list_markers}

        logger.debug(f"빈 STRProfile 생성 완료 (마커 수={len(dict_profile_set)})")
        return NFS_SP.STRProfile(id=samplename, profile=dict_profile_set)

    def update_profile_with_STRProfile(
        self, samplename: str, profile: NFS_SP.STRProfile
    ) -> None:
        """STRProfile 객체의 프로필 데이터를 DataFrame에 업데이트

        지정된 샘플명에 해당하는 행의 각 로커스 컬럼에 STRProfile의
        알릴 정보를 문자열 형태로 업데이트합니다.

        Args:
            samplename: 업데이트할 감정물 번호/샘플 이름
            profile: 업데이트할 프로필 데이터를 담은 STRProfile 객체

        Raises:
            ValueError: 샘플명이 데이터에서 찾을 수 없는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> str_profile = NFS_SP.STRProfile(id="S001", profile={"D3S1358": {"15", "16"}})
            >>> pdm.update_profile_with_STRProfile("S001", str_profile)
        """
        logger.debug(f"프로필 업데이트 시작 (samplename={samplename})")

        # 샘플 존재 여부 확인
        sample_mask = self.df_profile["감정물번호"] == samplename
        if not sample_mask.any():
            logger.error(f"샘플 '{samplename}'을 찾을 수 없습니다.")
            raise ValueError(f"샘플 '{samplename}'을 찾을 수 없습니다.")

        # STRProfile 데이터를 문자열로 변환
        profile_data = profile.export_to_str()

        # 각 로커스별 알릴 정보 업데이트
        for locus, allele in profile_data.items():
            self.df_profile.loc[sample_mask, locus] = allele

        logger.debug(f"프로필 업데이트 완료 (로커스 수={len(profile_data)})")

    def insert_new_profile_with_STRProfile(
        self, code_case: str, samplename: str, profile: NFS_SP.STRProfile
    ) -> None:
        """새로운 STRProfile을 DataFrame에 삽입

        지정된 접수번호와 샘플명으로 새로운 프로필 행을 생성하여
        DataFrame에 추가합니다. 이미 존재하는 샘플명인 경우 오류를 발생시킵니다.

        Args:
            code_case: 접수번호
            samplename: 감정물번호
            profile: 삽입할 STRProfile 객체

        Raises:
            ValueError: 샘플명이 이미 존재하는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> new_profile = NFS_SP.STRProfile(id="NEW-001", profile={"D3S1358": {"15", "16"}})
            >>> pdm.insert_new_profile_with_STRProfile("2025-C-1234", "NEW-001", new_profile)

        See Also:
            update_profile_with_STRProfile: 기존 프로필 업데이트용 메서드
        """
        logger.debug(f"새 프로필 삽입 시작 (code_case={code_case}, samplename={samplename})")

        # 샘플 존재 여부 확인
        sample_mask = self.df_profile["감정물번호"] == samplename
        if sample_mask.any():
            logger.error(f"샘플 '{samplename}'이 이미 존재합니다.")
            raise ValueError(
                f"'{samplename}'은 이미 존재합니다. "
                "update_profile_with_STRProfile를 이용하세요."
            )

        # 새 행 데이터 생성
        new_row = {
            "접수번호": code_case,
            "감정물번호": samplename,
            "STATUS_COMBINED": "UNIQUE",
        }

        # STRProfile 데이터를 문자열로 변환하여 추가
        profile_data = profile.export_to_str()
        new_row.update(profile_data)

        # DataFrame에 새 행 추가
        new_df = pd.DataFrame([new_row])
        self.df_profile = pd.concat(
            [self.df_profile, new_df], ignore_index=True
        )

        logger.debug(f"새 프로필 삽입 완료 (samplename={samplename}, 로커스 수={len(profile_data)})")

    def delete_profile_by_samplename(self, samplename: str) -> None:
        """샘플명으로 프로필 삭제

        지정된 샘플명에 해당하는 프로필을 DataFrame에서 삭제합니다.
        삭제 후 인덱스를 재정렬합니다.

        Args:
            samplename: 삭제할 감정물번호

        Raises:
            ValueError: 샘플명을 찾을 수 없는 경우

        Examples:
            >>> pdm = NFSProfileDataManager(kit="STR")
            >>> pdm.delete_profile_by_samplename("S001")
        """
        logger.debug(f"프로필 삭제 시작 (samplename={samplename})")

        # 해당 샘플 찾기
        sample_mask = self.df_profile["감정물번호"] == samplename

        if not sample_mask.any():
            logger.error(f"샘플 '{samplename}'을 찾을 수 없습니다.")
            raise ValueError(f"샘플 '{samplename}'을 찾을 수 없습니다.")

        # 행 삭제 및 인덱스 재정렬
        self.df_profile = self.df_profile[~sample_mask].reset_index(drop=True)

        logger.debug(f"프로필 삭제 완료 (samplename={samplename})")

    def generate_mix_profile(self, samplenames: list) -> NFS_SP.STRProfile:
        """
        여러 샘플의 STR 프로필을 결합하여 혼합 프로필을 생성합니다.

        빈 STR 프로필로 시작하여 각 샘플의 프로필을 순차적으로
        결합(union)하여 최종 혼합 프로필을 생성합니다.

        Args:
            samplenames (list[str]): 혼합할 샘플명들의 리스트

        Returns:
            STRProfile: 모든 입력 샘플들의 알릴이 결합된 혼합 프로필

        Raises:
            ValueError: samplenames가 비어있는 경우

        Examples:
            >>> mixed = analyzer.generate_mix_profile(["sample1", "sample2", "sample3"])
            >>> print(len(mixed.profile))  # 결합된 프로필의 마커 수
        """
        logger.info(f"혼합 프로필 생성 시작 (샘플 수={len(samplenames)})")
        # 입력 유효성 검사
        if not samplenames:
            logger.error("ValueError: 혼합할 샘플명 리스트가 비어있습니다.")
            raise ValueError("혼합할 샘플명 리스트가 비어있습니다.")

        # 빈 프로필로 시작
        mixed_profile = self.generate_empty_STRProfile()

        # 각 샘플의 프로필을 순차적으로 결합
        for samplename in samplenames:
            logger.debug(f"샘플 병합 중: {samplename}")
            element_profile = self.generate_STRProfile(samplename)
            mixed_profile = mixed_profile.union_profiles(element_profile)

        logger.info(f"혼합 프로필 생성 완료 (샘플 수={len(samplenames)}, 마커 수={len(mixed_profile.profile)})")
        return mixed_profile