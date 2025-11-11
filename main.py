import module.NFS_PROFILEDATAMANAGER as NFS_PM
import pandas as pd
import module.NFS_REPORTINFORMATION as NFS_RI

df_caseinfo = pd.read_csv('./testdata/test_df_caseinfo.csv')
df_report = pd.read_csv('./testdata/test_df_report.csv')
df_str = pd.read_csv('./testdata/test_df_profile_str.csv')
df_ystr = pd.read_csv('./testdata/test_df_profile_ystr.csv')
pm_str = NFS_PM.NFSProfileDataManager(kit="STR")
pm_str.df_profile = df_str
pm_ystr = NFS_PM.NFSProfileDataManager(kit='YSTR')
pm_ystr.df_profile = df_ystr

info = NFS_RI.NFSReportInformation(id_case='2025-C-6697')
info.extract_caseinfo_from_df(df_caseinfo)
info.extract_evidenceinfo_from_df(df_report)
info.load_str_profiledatamanager(pm_str)
info.load_ystr_profiledatamanager(pm_ystr)

