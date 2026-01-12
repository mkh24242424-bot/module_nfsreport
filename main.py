import logging
import os
import module.NFS_PROFILEDATAMANAGER as NFS_PM
import pandas as pd
import module.NFS_REPORTINFORMATION as NFS_RI
import module.NFS_REPORTWRITER as NFS_RW
import module.constants_reportwriter as REPORT_TYPER
import module.NFS_HWPFORMATTER as NFS_HWP
import module.NFS_BLOCKMANAGER as NFS_BM
from module.barcode_generator import generate_barcode_no_text

from datetime import datetime

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

logger.info("NFSReportInformation 객체 생성")
id_case = "2025-C-6845"
info = NFS_RI.NFSReportInformation(id_case=id_case)

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

type_report = "default"
logger.info("NFSReportWriter 객체 생성")
RW = NFS_RW.NFSReportWriter(info, blocks_manager_str, blocks_manager_ystr, type_report=type_report)

logger.info("한글 포맷터 객체 생성")
path_base = os.path.dirname(os.path.abspath(__file__))
hwp_formatter = NFS_HWP.NFS_HWPFormatter(path_base=path_base)

logger.info("새 감정서 생성")
hwp_formatter.create_new_report(code_case=info.id_case, type_report="DEFAULT")

logger.info("꼬리말 바코드 입력")
saved_path = generate_barcode_no_text(text=id_case, filename="barcode")
absolute_path = os.path.abspath(saved_path)
hwp_formatter.fill_barcode(path_barcode=absolute_path)
os.remove(absolute_path)

logger.info("사건 기본 정보 입력")
for field in info.caseinfo:
    hwp_formatter.fill_fieldtext(field_name=field, text=info.caseinfo[field])

logger.info("감정물명 입력")
evidence_text = RW.make_contents_evidence()
hwp_formatter.fill_fieldtext(field_name="감정물", text=evidence_text)

logger.info("실험방법 입력")
experiment_method = RW.make_contents_experiment_methods()
hwp_formatter.fill_fieldtext(field_name="실험방법", text=experiment_method)

logger.info("감정결과 입력")
phrase_result = RW.make_contents_result()
hwp_formatter.fill_fieldtext(field_name="실험결과", text=phrase_result)

logger.info("기타 내용 입력")
phrase_remark = RW.make_contents_remarks(phrase_result=phrase_result)
hwp_formatter.fill_fieldtext(field_name="기타", text=phrase_remark)

logger.info("날짜 입력")
# 오늘 날짜 가져오기
today = datetime.now()
# "2025년 10월 15일" 형식으로 포맷팅
formatted_date = f"{today.year}년 {today.month}월 {today.day}일"
hwp_formatter.fill_fieldtext(field_name="작성일", text=formatted_date)

logger.info("도장 입력")
sealinfo = [
    {"name": "문경환", "path_img": "/img/seal1.png"},
    {"name": "문경환", "path_img": "/img/seal2.png"},
    {"name": "문경환", "path_img": "/img/seal3.png"},
]
hwp_formatter.fill_seal(sealinfo=sealinfo)

logger.info("STR 프로필 표 입력")
serialized_profile, note_etc = RW.make_contents_profile_blocks(kit="STR20")
hwp_formatter.fill_fieldtext(field_name="STR프로필_기타", text=note_etc)
hwp_formatter.fill_table_profile(serialized_profile=serialized_profile, kit="STR20")

logger.info("YSTR 프로필 표 입력")
serialized_profile, note_etc = RW.make_contents_profile_blocks(kit="YSTR")
hwp_formatter.fill_fieldtext(field_name="YSTR프로필_기타", text=note_etc)
hwp_formatter.fill_table_profile(serialized_profile=serialized_profile, kit="YSTR")

logger.info("이미지 입력")
paths_img = ["C:/Users/mkh24/PycharmProjects/module_nfsreport/img/Pictures/2025-C-6745-1.JPG",
             "C:/Users/mkh24/PycharmProjects/module_nfsreport/img/Pictures/2025-C-6745-2.JPG",
             "C:/Users/mkh24/PycharmProjects/module_nfsreport/img/Pictures/2025-C-6745-3.JPG",
             "C:/Users/mkh24/PycharmProjects/module_nfsreport/img/Pictures/2025-C-6745-4.JPG",
             "C:/Users/mkh24/PycharmProjects/module_nfsreport/img/Pictures/2025-C-6745-5.JPG",]
hwp_formatter.insert_pictures(paths_img=paths_img)

hwp_formatter.save_and_move_to_firstpage()
logger.info("========== 프로그램 종료 ==========")




