import win32com.client as win32
from .constants_hwpformatter import PATH_HWP_TEMPLATE, NAME_FIELDTEXT, LIST_SEALFIELD
import os, shutil


class NFS_HWPFormatter:
    def __init__(self, path_base:str):
        self.hwp_control = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")  # type: ignore
        self.hwp_control.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")
        self.hwp_control.XHwpWindows.Item(0).Visible = True
        self.path_base = path_base
    
    def create_new_report(self, code_case: str, type_report: str="DEFAULT", ):
        path_template = f"{self.path_base}{ PATH_HWP_TEMPLATE[type_report]}"
        path_report = f"{self.path_base}/report/{code_case}.hwp"
        shutil.copyfile(path_template, path_report)
        self.hwp_control.Open(path_report)  # 문서 경로 지정
        self.hwp_control.Run("FrameFullScreen")  # 한글을 전체화면으로 만듭니다.
        self.hwp_control.Run("MoveDocBegin")
        
    def fill_fieldtext(self, field_name: str, text: str):
        if field_name in NAME_FIELDTEXT:
            self.hwp_control.PutFieldText(NAME_FIELDTEXT[field_name], text)
        else:
            raise ValueError(f"필드 이름 '{field_name}'이(가) 정의되어 있지 않습니다.") 

    def fill_seal(self, sealinfo:list[dict[str,str]]):
        for idx, seal in enumerate(sealinfo):
            if idx >= len(LIST_SEALFIELD):
                break
            field_name = LIST_SEALFIELD[idx].field_name
            field_img = LIST_SEALFIELD[idx].field_img
            name = seal['name'] if idx==0 else f", {seal['name']}" # 첫번째 도장 외에는 쉼표 추가
            path = f"{self.path_base}{seal['path_img']}"
            self.hwp_control.PutFieldText(field_name, name)
            self.hwp_control.MoveToField(field_img)
            self.hwp_control.InsertPicture(path, sizeoption=2) # 2: 필드 크기에 맞춤

    def save_and_quit(self, save_path: str):
        self.hwp_control.SaveAs(save_path)
        self.hwp_control.Quit()


