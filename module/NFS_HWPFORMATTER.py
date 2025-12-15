import win32com.client as win32
from .constants_hwpformatter import PATH_HWP_TEMPLATE, NAME_FIELDTEXT, LIST_SEALFIELD, KEYWORDS_PAIREDPROFILE, NAME_FIELDTABLE
from .constants_strprofile import DICT_MARKERS
import os, shutil
from typing import Literal

import time

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

    def fill_table_profile(self, serialized_profile:list[list], kit:Literal["STR", "STR20", "YSTR"]):
        def copy_empty_column():
            self.hwp_control.HAction.Run("TableCellBlock")
            time.sleep(2)
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            time.sleep(2)
            self.hwp_control.HAction.Run("TableColPageDown")
            time.sleep(2)
            self.hwp_control.HAction.Run("Copy")
            time.sleep(2)
            self.hwp_control.HAction.Run("TableColPageUp")
            time.sleep(2)
            self.hwp_control.HAction.GetDefault("Paste", self.hwp_control.HParameterSet.HSelectionOpt.HSet)
            self.hwp_control.HParameterSet.HSelectionOpt.option = 1
            self.hwp_control.HAction.Execute("Paste", self.hwp_control.HParameterSet.HSelectionOpt.HSet)
            time.sleep(2)
        def split_headline():
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableRightCell")
            self.hwp_control.HAction.GetDefault("TableSplitCell", self.hwp_control.HParameterSet.HTableSplitCell.HSet)
            self.hwp_control.HParameterSet.HTableSplitCell.Cols = 0
            self.hwp_control.HAction.Execute("TableSplitCell", self.hwp_control.HParameterSet.HTableSplitCell.HSet)
            self.hwp_control.HAction.Run("Cancel")
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableLeftCell")
            self.hwp_control.HAction.Run("TableMergeCell")
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableLowerCell")
            self.hwp_control.HAction.Run("TableDistributeCellHeight")
            self.hwp_control.HAction.Run("Cancel")
            self.hwp_control.HAction.Run("MoveUp")
        
        def input_text(text):
            self.hwp_control.HAction.GetDefault("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
            self.hwp_control.HParameterSet.HInsertText.Text = text
            self.hwp_control.HAction.Execute("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
        
        def input_list_text_vertically(list_text):
            for value in list_text:
                input_text(value)
                self.hwp_control.HAction.Run("MoveDown")
            self.hwp_control.HAction.Run("MoveUp")
        
        def move_to_next_column():
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableColPageUp")
            self.hwp_control.HAction.Run("TableRightCell")
            self.hwp_control.HAction.Run("Cancel")

        markers = DICT_MARKERS[kit]

        # YSTR 데이터가 없으면 표 삭제
        if kit=="YSTR" and len(serialized_profile)==0:  
            self.hwp_control.MoveToField(NAME_FIELDTABLE["TABLE_YSTR_FIRSTCELL"])
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("Delete")  
            return
        
        # 표의 첫번째 데이터 칼럼 셀로 이동
        if kit in ["STR", "STR20"]:
            self.hwp_control.MoveToField(NAME_FIELDTABLE["STR_FIRSTCOL"])
        elif kit == "YSTR":
            self.hwp_control.MoveToField(NAME_FIELDTABLE["YSTR_FIRSTCOL"])
        
        for block in serialized_profile:
            # 프로필 표의 칼럼 복사
            copy_empty_column()
            if any(item in KEYWORDS_PAIREDPROFILE for item in block): #페어 프로필 입력
                split_headline()
                input_text(block[0]) # paired profile의 증거물 번호(증1호)
                # 첫번째 프로필 입력란으로 이동
                self.hwp_control.HAction.Run("MoveDown")
                self.hwp_control.HAction.Run("MoveLeft")
                idx_start_second_profile = 2+len(markers)
                input_list_text_vertically(block[1:idx_start_second_profile])
                # 두번째 프로필 입력란으로 이동
                self.hwp_control.HAction.Run("TableCellBlock")
                self.hwp_control.HAction.Run("TableRightCell")
                self.hwp_control.HAction.Run("TableColPageUp")
                self.hwp_control.HAction.Run("Cancel")
                self.hwp_control.HAction.Run("MoveDown")
                input_list_text_vertically(block[idx_start_second_profile:])
                move_to_next_column()
            else: # 일반 입력
                input_list_text_vertically(block)
                move_to_next_column()
        # 빈 칼럼 삭제
        self.hwp_control.HAction.Run("TableCellBlock")
        self.hwp_control.HAction.Run("TableCellBlockExtend")
        self.hwp_control.HAction.Run("TableColPageDown")
        self.hwp_control.HAction.Run("TableDeleteCell")

    def save_and_quit(self, save_path: str):
        self.hwp_control.SaveAs(save_path)
        self.hwp_control.Quit()


