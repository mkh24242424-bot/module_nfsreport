import logging
from . import NFS_PROFILEDATAMANAGER as NFS_PM
import pandas as pd

logger = logging.getLogger(__name__)

class NFSReportInformation():
    """국립과학수사연구원 유전자과 감정서에 필요한 한 사건의 정보를 모아서 정리하는 데이터클래스"""
    def __init__(self, id_case:str = "noname", type_case:str = "default"):
        logger.info(f"NFSReportInformation 초기화 (id_case={id_case}, type_case={type_case})")
        self.id_case = id_case
        self.type_case = type_case
        self.caseinfo:dict = {}
        self.evidenceinfo:pd.DataFrame = pd.DataFrame()
        self.pm_str = None
        self.pm_ystr = None
        logger.debug("NFSReportInformation 초기화 완료")

    def extract_caseinfo_from_df(self, df_caseinfo:pd.DataFrame):
        """사건정보 데이터프레임에서 사건번호에 해당하는 사건정보 중 감정서에 필요한 데이터 추출해서 딕셔너리화"""
        logger.debug(f"사건정보 추출 시작 (id_case={self.id_case})")
        list_required_columns = ['의뢰관서', '문서번호', '접수일자', '시행일자']
        try:
            self.caseinfo = df_caseinfo.loc[df_caseinfo['접수번호']==self.id_case, list_required_columns].iloc[0].to_dict()
            logger.info(f"사건정보 추출 완료 (id_case={self.id_case}, 필드 수={len(self.caseinfo)})")
        except KeyError as e:
            logger.error(f"KeyError: {e} - {self.id_case}의 사건 정보가 데이터프레임에 존재하지 않습니다.")
            print(f"{e} : {self.id_case}의 사건 정보가 데이터프레임에 존재하지 않습니다.")
            
    def extract_evidenceinfo_from_df(self, df_evidenceinfo:pd.DataFrame):
        logger.debug(f"증거물 정보 추출 시작 (id_case={self.id_case})")
        list_required_columns = ['접수번호', '감정물번호', '감정물', '분류', '대조_이름', 'Y_대조_이름', '프로필_유형',
                                 'Y_프로필_유형', '코드', 'Y_코드', '표기번호', 'Y_표기번호', '기재_여부', 'Y_기재_여부',
                                   '타액_반응', '정액_반응', '혈흔_반응', '검색_결과', '반환_여부']
        try:
            self.evidenceinfo = df_evidenceinfo.loc[df_evidenceinfo['접수번호']==self.id_case, list_required_columns].reset_index(drop=True)
            logger.info(f"증거물 정보 추출 완료 (id_case={self.id_case}, 증거물 수={len(self.evidenceinfo)})")
        except KeyError as e:
            logger.error(f"KeyError: {e} - {self.id_case}의 사건 정보가 데이터프레임에 존재하지 않습니다.")
            print(f"{e} : {self.id_case}의 사건 정보가 데이터프레임에 존재하지 않습니다.")
    
    def load_str_profiledatamanager(self, pdm: NFS_PM.NFSProfileDataManager):
        logger.debug(f"STR 프로필 데이터 매니저 로딩 시작 (id_case={self.id_case})")
        self.pm_str = pdm.filter_by_codecase(code_case = self.id_case)
        if self.pm_str:
            logger.info(f"STR 프로필 데이터 매니저 로딩 완료 (프로필 수={len(self.pm_str.df_profile)})")
        else:
            logger.warning("STR 프로필 데이터 매니저 로딩 실패 (프로필 없음)")

    def load_ystr_profiledatamanager(self, pdm: NFS_PM.NFSProfileDataManager):
        logger.debug(f"YSTR 프로필 데이터 매니저 로딩 시작 (id_case={self.id_case})")
        self.pm_ystr = pdm.filter_by_codecase(code_case = self.id_case)
        if self.pm_ystr:
            logger.info(f"YSTR 프로필 데이터 매니저 로딩 완료 (프로필 수={len(self.pm_ystr.df_profile)})")
        else:
            logger.warning("YSTR 프로필 데이터 매니저 로딩 실패 (프로필 없음)")