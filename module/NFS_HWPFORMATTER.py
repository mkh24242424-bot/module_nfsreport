import win32com.client as win32
from .constants_hwpformatter import PATH_HWP_TEMPLATE, NAME_CELLFIELD
import os, shutil


class NFS_HWPFormatter:
    def __init__(self, type_report: str, path_base:str, code_case: str, ):
        self.hwp_control = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")  # type: ignore
        self.hwp_control.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")
        self.hwp_control.XHwpWindows.Item(0).Visible = True
        path_template = path_base + PATH_HWP_TEMPLATE[type_report]
        path_report = path_base + f"/report/{code_case}.hwp"
        shutil.copyfile(path_template, path_report)
        self.hwp_control.Open(path_report)  # 문서 경로 지정
        self.hwp_control.Run("FrameFullScreen")  # 한글을 전체화면으로 만듭니다.
        self.hwp_control.Run("MoveDocBegin")
        
    
    def fill_field_caseinfo(self, caseinfo: dict[str, str]):
        for field, value in NAME_CELLFIELD.items():
            if field in caseinfo:
                self.hwp_control.PutFieldText(value, caseinfo[field])
        

    def save_and_quit(self, save_path: str):
        self.hwp_control.SaveAs(save_path)
        self.hwp_control.Quit()


