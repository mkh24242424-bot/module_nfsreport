import logging
import os
import module.NFS_PROFILEDATAMANAGER as NFS_PM
import pandas as pd
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.constants_reportwriter as REPORT_TYPER
import module.NFS_HWPFORMATTER as NFS_HWP
import module.NFS_BLOCKMANAGER as NFS_BM

# 로깅 설정
logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

logger.info("========== 프로그램 시작 ==========")

logger.info("CSV 파일 읽기 시작: ./testdata/test_df_caseinfo.csv")
df_caseinfo = pd.read_csv('./testdata/test_df_caseinfo.csv')
logger.info(f"CSV 파일 읽기 완료 ({len(df_caseinfo)} rows)")

logger.info("CSV 파일 읽기 시작: ./testdata/test_df_report.csv")
df_report = pd.read_csv('./testdata/test_df_report.csv')
logger.info(f"CSV 파일 읽기 완료 ({len(df_report)} rows)")

logger.info("CSV 파일 읽기 시작: ./testdata/test_df_profile_str.csv")
df_str = pd.read_csv('./testdata/test_df_profile_str.csv')
logger.info(f"CSV 파일 읽기 완료 ({len(df_str)} rows)")

logger.info("CSV 파일 읽기 시작: ./testdata/test_df_profile_ystr.csv")
df_ystr = pd.read_csv('./testdata/test_df_profile_ystr.csv')
logger.info(f"CSV 파일 읽기 완료 ({len(df_ystr)} rows)")

logger.info("NFSProfileDataManager 생성 (kit=STR)")
pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
pm_str.df_profile = df_str
logger.debug(f"STR 프로필 데이터 로드 완료 ({len(df_str)} profiles)")

logger.info("NFSProfileDataManager 생성 (kit=YSTR)")
pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
pm_ystr.df_profile = df_ystr
logger.debug(f"YSTR 프로필 데이터 로드 완료 ({len(df_ystr)} profiles)")

logger.info("NFSReportInformation 객체 생성 (id_case=2025-C-6745)")
info = NFS_RI.NFSReportInformation(id_case='2025-C-6698')

logger.info("사건 정보 추출 시작")
info.extract_caseinfo_from_df(df_caseinfo)

logger.info("증거물 정보 추출 시작")
info.extract_evidenceinfo_from_df(df_report)

logger.info("STR 프로필 데이터 매니저 로딩")
info.load_str_profiledatamanager(pm_str)

logger.info("YSTR 프로필 데이터 매니저 로딩")
info.load_ystr_profiledatamanager(pm_ystr)

logger.info("STR 블록 매니저 생성")
info_written_str = info.evidenceinfo[
    info.evidenceinfo["기재_여부"] == "기재"
]
logger.debug(f"STR 기재 증거물 수: {len(info_written_str)}")

blocks_manager_str = NFS_BM.BlockProfileManager(
    info_written=info_written_str,
    kit='STR'
)
blocks_manager_str.generate_blocks()

logger.info("Y-STR 블록 매니저 생성")
info_written_ystr = info.evidenceinfo[
    info.evidenceinfo["Y_기재_여부"] == "기재"
]
logger.debug(f"Y-STR 기재 증거물 수: {len(info_written_ystr)}")
blocks_manager_ystr = NFS_BM.BlockProfileManager(
    info_written=info_written_ystr,
    kit='YSTR'
)
blocks_manager_ystr.generate_blocks()

logger.info("NFSReportWriter 객체 생성")
RW = NFS_RW.NFSReportWriter(info, blocks_manager_str, blocks_manager_ystr)

logger.info("프로필 분류 시작")
RW.make_contents_result(REPORT_TYPER.REPORT_TYPE_PHRASERS["deceased_only"])
print(RW.phrases_result)
#----------------------------------------------------------
logger.info("한글 포맷터 객체 생성")
path_base = os.path.dirname(os.path.abspath(__file__))
hwp_formatter = NFS_HWP.NFS_HWPFormatter(type_report="DEFAULT", path_base=path_base, code_case=info.id_case)


logger.info("========== 프로그램 종료 ==========")


