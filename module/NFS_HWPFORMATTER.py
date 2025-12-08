import win32com.client as win32
from .constants_hwpformatter import PATH_HWP_TEMPLATE
import os, shutil


class NFS_HWPFormatter:
    def __init__(self, type_report: str, path_base:str, code_case: str):
        self.hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")  # type: ignore
        self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")
        self.hwp.XHwpWindows.Item(0).Visible = True
        path_template = path_base + PATH_HWP_TEMPLATE[type_report]
        path_report = path_base + f"/report/{code_case}.hwp"
        shutil.copyfile(path_template, path_report)
        self.hwp.Open(path_report)  # 문서 경로 지정
        self.hwp.Run("FrameFullScreen")  # 한글을 전체화면으로 만듭니다.
    
    def save_and_quit(self, save_path: str):
        self.hwp.SaveAs(save_path)
        self.hwp.Quit()


