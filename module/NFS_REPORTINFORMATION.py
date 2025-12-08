import logging
from . import NFS_PROFILEDATAMANAGER as NFS_PM
from .exceptions import CaseNotFoundError
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class NFSReportInformation:
    """국립과학수사연구원(NFS) DNA 감정서 작성을 위한 사건 정보 관리 클래스

    한 사건에 필요한 모든 정보(사건 메타데이터, 증거물 정보, 프로필 데이터)를
    수집하고 관리하는 데이터 클래스입니다.

    주요 기능:
        - 사건 정보 추출 및 저장
        - 증거물 정보 추출 및 저장
        - STR/Y-STR 프로필 데이터 매니저 로딩

    Attributes:
        id_case: 사건번호 (예: '2025-C-1234')
        report_type: 감정서 종류 (default, deceased, suspect, paternity 등)
        caseinfo: 사건 메타데이터 딕셔너리 (의뢰관서, 문서번호, 접수일자, 시행일자)
        evidenceinfo: 증거물 정보 DataFrame
        pm_str: STR 프로필 데이터 매니저 (NFSProfileDataManager 또는 None)
        pm_ystr: Y-STR 프로필 데이터 매니저 (NFSProfileDataManager 또는 None)

    Examples:
        >>> info = NFSReportInformation(id_case='2025-C-1234')
        >>> info.extract_caseinfo_from_df(df_caseinfo)
        >>> info.extract_evidenceinfo_from_df(df_report)
        >>> info.load_str_profiledatamanager(pdm_str)

    See Also:
        NFSProfileDataManager: 프로필 데이터 관리 클래스
        NFSReportWriter: 감정서 작성 클래스
    """

    # 인스턴스 변수 타입 힌트
    id_case: str
    report_type: str
    caseinfo: dict
    evidenceinfo: pd.DataFrame
    pm_str: NFS_PM.NFSProfileDataManager | None
    pm_ystr: NFS_PM.NFSProfileDataManager | None

    def __init__(self, id_case: str = "noname", report_type: str = "default"):
        """NFSReportInformation 초기화

        Args:
            id_case: 사건번호. 기본값은 "noname"
            report_type: 감정서 종류 (default, deceased, suspect, paternity 등). 기본값은 "default"

        Examples:
            >>> info = NFSReportInformation(id_case='2025-C-1234')
            >>> info = NFSReportInformation(id_case='2025-C-5678', report_type='suspect')
        """
        logger.info(f"NFSReportInformation 초기화 (id_case={id_case}, report_type={report_type})")

        self.id_case = id_case
        self.report_type = report_type
        self.caseinfo = {}
        self.evidenceinfo = pd.DataFrame()
        self.pm_str = None
        self.pm_ystr = None

    def extract_caseinfo_from_df(self, df_caseinfo: pd.DataFrame) -> None:
        """DataFrame에서 사건번호에 해당하는 사건 정보 추출

        사건정보 DataFrame에서 현재 사건번호(id_case)에 해당하는 행을 찾아
        감정서 작성에 필요한 사건 정보를 추출하여 딕셔너리로 저장합니다.

        Args:
            df_caseinfo: 사건 정보가 담긴 DataFrame (필수 컬럼 포함 필요)

        Raises:
            CaseNotFoundError: 사건번호가 존재하지 않거나 필수 컬럼이 누락된 경우

        Note:
            추출된 데이터는 self.caseinfo에 딕셔너리로 저장됩니다.

        Examples:
            >>> info = NFSReportInformation(id_case='2025-C-1234')
            >>> info.extract_caseinfo_from_df(df_caseinfo)
            >>> print(info.caseinfo['의뢰관서'])
            '서울지방경찰청'
        """
        logger.debug(f"사건정보 추출 시작 (id_case={self.id_case})")

        # 1. 필수 컬럼 정의
        required_columns = ['의뢰관서', '문서번호', '접수일자', '시행일자', '접수번호']

        # 2. 필수 컬럼 존재 여부 검증
        missing_columns = set(required_columns) - set(df_caseinfo.columns)
        if missing_columns:
            logger.error(f"사건정보 추출 실패: 필수 컬럼 누락 - {missing_columns}")
            raise CaseNotFoundError(
                self.id_case,
                f"사건정보 추출 실패: 필수 컬럼 누락 - {missing_columns}"
            )

        # 3. '접수번호' 컬럼 존재 여부 검증
        if '접수번호' not in df_caseinfo.columns:
            logger.error("사건정보 추출 실패: '접수번호' 컬럼이 존재하지 않습니다")
            raise CaseNotFoundError(
                self.id_case,
                "사건정보 추출 실패: '접수번호' 컬럼이 존재하지 않습니다"
            )

        # 4. 사건번호로 필터링
        try:
            case_mask = df_caseinfo['접수번호'] == self.id_case
            filtered_df = df_caseinfo.loc[case_mask, required_columns]

            # 5. 결과 존재 여부 확인
            if filtered_df.empty:
                logger.error(f"사건번호 '{self.id_case}'에 해당하는 사건정보가 없습니다")
                raise CaseNotFoundError(
                    self.id_case,
                    "사건정보가 존재하지 않습니다"
                )

            # 6. 첫 번째 행을 딕셔너리로 변환 및 저장
            self.caseinfo = filtered_df.iloc[0].to_dict()

            # 7. 결과를 감정서에 쓰이는 포멧으로 변환
            # 접수일자와 시행일자를 '년 월 일' 형식으로 변환, 문서번호와 접수번호에 '호' 추가
            for date_field in ['접수일자', '시행일자']:
                date_obj = datetime.strptime(self.caseinfo[date_field], "%Y.%m.%d")
                self.caseinfo[date_field] = f"({date_obj.year}년 {date_obj.month}월 {date_obj.day}일)"
            for date_field in ['문서번호', '접수번호']:
                self.caseinfo[date_field] = self.caseinfo[date_field] + '호'

            logger.info(
                f"사건정보 추출 완료 (id_case={self.id_case}, "
                f"필드 수={len(self.caseinfo)})"
            )

        except KeyError as e:
            logger.error(f"사건정보 추출 중 예상치 못한 오류: {e}")
            raise CaseNotFoundError(
                self.id_case,
                f"사건정보 추출 실패: {e}"
            ) from e
        except IndexError as e:
            logger.error(f"사건번호 '{self.id_case}'에 해당하는 사건정보가 없습니다")
            raise CaseNotFoundError(
                self.id_case,
                "사건정보가 존재하지 않습니다"
            ) from e
            
    def extract_evidenceinfo_from_df(self, df_evidenceinfo: pd.DataFrame) -> None:
        """DataFrame에서 사건번호에 해당하는 증거물 정보 추출

        증거물 정보 DataFrame에서 현재 사건번호(id_case)에 해당하는 행들을 필터링하여
        감정서 작성에 필요한 증거물 정보를 추출합니다.

        Args:
            df_evidenceinfo: 증거물 정보가 담긴 DataFrame (필수 컬럼 포함 필요)

        Raises:
            CaseNotFoundError: 필수 컬럼이 누락된 경우

        Note:
            추출된 데이터는 self.evidenceinfo에 저장됩니다.
            DataFrame 인덱스는 재설정됩니다 (0부터 시작).
            사건번호에 해당하는 증거물이 없으면 빈 DataFrame이 저장됩니다.

        Examples:
            >>> info = NFSReportInformation(id_case='2025-C-1234')
            >>> info.extract_evidenceinfo_from_df(df_report)
            >>> print(len(info.evidenceinfo))
            5
        """
        logger.debug(f"증거물 정보 추출 시작 (id_case={self.id_case})")

        # 1. 필수 컬럼 정의
        required_columns = [
            '접수번호', '감정물번호', '감정물', '분류',
            '대조_이름', 'Y_대조_이름',
            '프로필_유형', 'Y_프로필_유형',
            '코드', 'Y_코드',
            '표기번호', 'Y_표기번호',
            '기재_여부', 'Y_기재_여부',
            '타액_반응', '정액_반응', '혈흔_반응',
            '검색_결과', '반환_여부'
        ]

        # 2. 필수 컬럼 존재 여부 검증
        missing_columns = set(required_columns) - set(df_evidenceinfo.columns)
        if missing_columns:
            logger.error(f"증거물 정보 추출 실패: 필수 컬럼 누락 - {missing_columns}")
            raise CaseNotFoundError(
                self.id_case,
                f"증거물 정보 추출 실패: 필수 컬럼 누락 - {missing_columns}"
            )

        # 3. 사건번호로 필터링
        try:
            case_mask = df_evidenceinfo['접수번호'] == self.id_case
            filtered_df = df_evidenceinfo.loc[case_mask, required_columns]

            # 4. 인덱스 재설정 및 저장
            self.evidenceinfo = filtered_df.reset_index(drop=True)

            # 5. 결과 로깅
            if self.evidenceinfo.empty:
                logger.warning(f"사건번호 '{self.id_case}'에 해당하는 증거물 정보가 없습니다")
            else:
                logger.info(
                    f"증거물 정보 추출 완료 (id_case={self.id_case}, "
                    f"증거물 수={len(self.evidenceinfo)})"
                )

        except KeyError as e:
            logger.error(f"증거물 정보 추출 중 예상치 못한 오류: {e}")
            raise CaseNotFoundError(
                self.id_case,
                f"증거물 정보 추출 실패: {e}"
            ) from e
    
    def load_str_profiledatamanager(self, profile_data_manager: NFS_PM.NFSProfileDataManager) -> None:
        """STR 프로필 데이터 매니저 로딩

        현재 사건번호에 해당하는 STR 프로필 데이터만 필터링하여 로딩합니다.

        Args:
            profile_data_manager: STR 프로필 데이터를 담고 있는 NFSProfileDataManager 인스턴스

        Note:
            필터링된 데이터는 self.pm_str에 저장됩니다.
            사건번호에 해당하는 프로필이 없으면 None이 저장됩니다.

        Examples:
            >>> info = NFSReportInformation(id_case='2025-C-1234')
            >>> pdm_str = NFSProfileDataManager(kit='STR')
            >>> info.load_str_profiledatamanager(pdm_str)
        """
        logger.debug(f"STR 프로필 데이터 매니저 로딩 시작 (id_case={self.id_case})")

        self.pm_str = profile_data_manager.filter_by_codecase(code_case=self.id_case)

        if self.pm_str is not None:
            logger.info(
                f"STR 프로필 데이터 매니저 로딩 완료 "
                f"(프로필 수={len(self.pm_str.df_profile)})"
            )
        else:
            logger.warning("STR 프로필 데이터 매니저 로딩 실패 (프로필 없음)")

    def load_ystr_profiledatamanager(self, profile_data_manager: NFS_PM.NFSProfileDataManager) -> None:
        """Y-STR 프로필 데이터 매니저 로딩

        현재 사건번호에 해당하는 Y-STR 프로필 데이터만 필터링하여 로딩합니다.

        Args:
            profile_data_manager: Y-STR 프로필 데이터를 담고 있는 NFSProfileDataManager 인스턴스

        Note:
            필터링된 데이터는 self.pm_ystr에 저장됩니다.
            사건번호에 해당하는 프로필이 없으면 None이 저장됩니다.

        Examples:
            >>> info = NFSReportInformation(id_case='2025-C-1234')
            >>> pdm_ystr = NFSProfileDataManager(kit='YSTR')
            >>> info.load_ystr_profiledatamanager(pdm_ystr)
        """
        logger.debug(f"YSTR 프로필 데이터 매니저 로딩 시작 (id_case={self.id_case})")

        self.pm_ystr = profile_data_manager.filter_by_codecase(code_case=self.id_case)

        if self.pm_ystr is not None:
            logger.info(
                f"YSTR 프로필 데이터 매니저 로딩 완료 "
                f"(프로필 수={len(self.pm_ystr.df_profile)})"
            )
        else:
            logger.warning("YSTR 프로필 데이터 매니저 로딩 실패 (프로필 없음)")