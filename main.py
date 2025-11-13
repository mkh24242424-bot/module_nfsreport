import logging
import module.NFS_PROFILEDATAMANAGER as NFS_PM
import pandas as pd
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.NFS_REPORTPHRASER as NFS_RP

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
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

logger.info("NFSReportInformation 객체 생성 (id_case=2025-C-6697)")
info = NFS_RI.NFSReportInformation(id_case='2025-C-6697')

logger.info("사건 정보 추출 시작")
info.extract_caseinfo_from_df(df_caseinfo)

logger.info("증거물 정보 추출 시작")
info.extract_evidenceinfo_from_df(df_report)

logger.info("STR 프로필 데이터 매니저 로딩")
info.load_str_profiledatamanager(pm_str)

logger.info("YSTR 프로필 데이터 매니저 로딩")
info.load_ystr_profiledatamanager(pm_ystr)

logger.info("NFSReportWriter 객체 생성")
RW = NFS_RW.NFSReportWriter(info, [])

logger.info("프로필 분류 시작")
RW.categorize_profiles()

logger.info("대조 프로필 문구 생성 시작")
RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_ref, type_profile='대조')

logger.info("대표 프로필 문구 생성 시작")
RW.make_contents_with_profile(phraser=NFS_RP.make_phrase_res, type_profile='대표')

logger.info("ND 프로필 문구 생성 시작")
RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nd, type_profile='ND')

logger.info("NC 프로필 문구 생성 시작")
RW.make_contents_without_profile(phraser=NFS_RP.make_phrase_nc, type_profile='NC')

logger.info(f"생성된 프로필 블록 수: {len(RW.profile_blocks)}")
print(RW.profile_blocks)

logger.info("========== 프로그램 종료 ==========")


