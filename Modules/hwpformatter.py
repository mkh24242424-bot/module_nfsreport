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
        self.path_report = ""
    
    def create_new_report(self, code_case: str, type_report: str="DEFAULT", ):
        path_template = f"{self.path_base}{ PATH_HWP_TEMPLATE[type_report]}"
        self.path_report = f"{self.path_base}/report/{code_case}.hwp"
        shutil.copyfile(path_template, self.path_report)
        self.hwp_control.Open(self.path_report)  # 문서 경로 지정
        self.hwp_control.Run("FrameFullScreen")  # 한글을 전체화면으로 만듭니다.
        self.hwp_control.Run("MoveDocBegin")
        
    def fill_fieldtext(self, field_name: str, text: str):
        if field_name in NAME_FIELDTEXT:
            self.hwp_control.PutFieldText(NAME_FIELDTEXT[field_name], text)
        else:
            raise ValueError(f"필드 이름 '{field_name}'이(가) 정의되어 있지 않습니다.") 

    def fill_barcode(self, path_barcode:str):
        self.hwp_control.MoveToField(NAME_FIELDTABLE["TABLE_BARCODE"])
        self.hwp_control.InsertPicture(path_barcode, sizeoption=2) # 2: 필드 크기에 맞춤

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
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableColPageDown")
            self.hwp_control.HAction.Run("Copy")
            self.hwp_control.HAction.Run("TableColPageUp")
            self.hwp_control.HAction.GetDefault("Paste", self.hwp_control.HParameterSet.HSelectionOpt.HSet)
            self.hwp_control.HParameterSet.HSelectionOpt.option = 1
            self.hwp_control.HAction.Execute("Paste", self.hwp_control.HParameterSet.HSelectionOpt.HSet)
        
        def split_headline():
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableRightCell")
            self.hwp_control.HAction.GetDefault("TableSplitCell", self.hwp_control.HParameterSet.HTableSplitCell.HSet)
            self.hwp_control.HParameterSet.HTableSplitCell.Rows = 2
            self.hwp_control.HParameterSet.HTableSplitCell.DistributeHeight = 1
            self.hwp_control.HAction.Execute("TableSplitCell", self.hwp_control.HParameterSet.HTableSplitCell.HSet)
            self.hwp_control.HAction.Run("TableColPageUp")
            self.hwp_control.HAction.Run("Cancel")
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableLeftCell")
            self.hwp_control.HAction.Run("TableMergeCell")
        
        def input_text(text):
            if '*' not in text:
                self.hwp_control.HAction.GetDefault("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
                self.hwp_control.HParameterSet.HInsertText.Text = text
                self.hwp_control.HAction.Execute("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
            else:
                parts = text.split('*')
                for i, part in enumerate(parts):
                    if part:  # 일반 텍스트 입력
                        self.hwp_control.HAction.GetDefault("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
                        self.hwp_control.HParameterSet.HInsertText.Text = part
                        self.hwp_control.HAction.Execute("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
                    if i < len(parts) - 1:  # * 입력 (위첨자)
                        # 위첨자 설정
                        prop = self.hwp_control.CharShape
                        prop.SetItem("SuperScript", True)
                        self.hwp_control.CharShape = prop
                        # * 입력
                        self.hwp_control.HAction.GetDefault("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
                        self.hwp_control.HParameterSet.HInsertText.Text = '*'
                        self.hwp_control.HAction.Execute("InsertText", self.hwp_control.HParameterSet.HInsertText.HSet)
                        # 위첨자 해제
                        prop = self.hwp_control.CharShape
                        prop.SetItem("SuperScript", False)
                        self.hwp_control.CharShape = prop
        
        def input_list_text_vertically(list_text):
            for value in list_text:
                input_text(value)
                # self.hwp_control.HAction.Run("MoveDown") # 테이블 크기가 페이지를 넘어가면 MoveDown 사용 시 오류 발생. 아래 방법이 속도는 느리지만 더 로버스트함.
                self.hwp_control.HAction.Run("TableCellBlock")
                self.hwp_control.HAction.Run("TableLowerCell")
                self.hwp_control.HAction.Run("Cancel")
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableUpperCell")
            self.hwp_control.HAction.Run("Cancel")
        
        def move_to_next_column():
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableColPageUp")
            self.hwp_control.HAction.Run("TableRightCell")
            self.hwp_control.HAction.Run("Cancel")

        markers = DICT_MARKERS[kit]

        # 데이터가 없으면 조기 반환
        if len(serialized_profile)==0:  
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
                copy_empty_column()
                split_headline()
                input_text(block[0]) # paired profile의 증거물 번호(증1호)
                # 첫번째 프로필 입력란으로 이동
                self.hwp_control.HAction.Run("TableCellBlock")
                self.hwp_control.HAction.Run("TableLowerCell")
                self.hwp_control.HAction.Run("Cancel")
                idx_start_second_profile = 2+len(markers)
                input_list_text_vertically(block[1:idx_start_second_profile])
                # 두번째 프로필 입력란으로 이동
                self.hwp_control.HAction.Run("TableCellBlock")
                self.hwp_control.HAction.Run("TableColPageUp")                
                self.hwp_control.HAction.Run("TableLowerCell")
                self.hwp_control.HAction.Run("TableRightCell")
                self.hwp_control.HAction.Run("Cancel")
                input_list_text_vertically(block[idx_start_second_profile:])
            else: # 일반 입력
                input_list_text_vertically(block)
            move_to_next_column()
        # 빈 칼럼 삭제
        self.hwp_control.SetMessageBoxMode(0x2000) #메시지 박스 지우기 자동선택
        self.hwp_control.HAction.Run("TableCellBlock")
        self.hwp_control.HAction.Run("TableCellBlockExtend")
        self.hwp_control.HAction.Run("TableColPageDown")
        self.hwp_control.HAction.Run("TableDeleteCell")
        self.hwp_control.SetMessageBoxMode(0xF000) #메시지 박스 초기화

    def _format_evidence_subnumber(self, filepath: str) -> str:
        """
        증거물 파일명에서 subnumber를 추출하여 법적 표기 형식으로 변환합니다.
        
        증거물 파일명 형식: {년도}-{사건구분}-{사건번호}-{subnumber}.{확장자}
        예: 2025-D-334-1-1.pdf
        
        Args:
            filepath: 증거물 파일 경로 (예: "2025-D-334-1-1.pdf")
        
        Returns:
            법적 표기 형식의 증거물 번호 (예: "증1-1호")
        
        변환 규칙:
            - 기본: "2025-D-334-1-1.pdf" → "증1-1호"
            - 범위(+): "2025-D-334-1-1+1-3.pdf" → "증1-1호~증1-3호"
            - 나열(,): "2025-D-334-1-1,2-1.pdf" → "증1-1호, 증2-1호"
            - 복합: "2025-D-334-1-1+1-3,2-1.pdf" → "증1-1호~증1-3호, 증2-1호"
        
        Examples:
            >>> format_evidence_subnumber("2025-D-334-1-1.pdf")
            '증1-1호'
            >>> format_evidence_subnumber("2025-D-334-1-1+1-3.pdf")
            '증1-1호~증1-3호'
        """
        # 1. 확장자 제거: "2025-D-334-1-1.pdf" → "2025-D-334-1-1"
        basename = filepath.rsplit(".", 1)[0]
        
        # 2. subnumber 추출: "2025-D-334-1-1" → "1-1"
        #    앞의 3개 요소(년도, 사건구분, 사건번호)를 제외한 나머지
        subnumber = "-".join(basename.split("-")[3:])
        
        # 3. 쉼표(,)로 구분된 각 그룹을 처리
        #    예: "1-1,2-1" → ["1-1", "2-1"]
        formatted_parts = []
        for group in subnumber.split(","):
            # 4. 플러스(+)로 구분된 범위를 처리
            #    예: "1-1+1-3" → ["1-1", "1-3"]
            range_items = [f"증{item}호" for item in group.split("+")]
            
            # 5. 범위는 물결표(~)로 연결
            #    예: ["증1-1호", "증1-3호"] → "증1-1호~증1-3호"
            formatted_parts.append("~".join(range_items))
        
        # 6. 그룹들은 쉼표로 연결
        #    예: ["증1-1호~증1-3호", "증2-1호"] → "증1-1호~증1-3호, 증2-1호"
        return ", ".join(formatted_parts)

    def insert_pictures(self, paths_img:list):
        num_img = len(paths_img)
        if num_img==0:
            return
        elif num_img==1: # 이미지가 하나면 단일 이미지용 테이블 사용. 다수 이미지용 테이블은 삭제
            self.hwp_control.MoveToField(NAME_FIELDTABLE["TABLE_IMG_MULTI_FIRSTCELL"])
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("Delete")  
            self.hwp_control.MoveToField(NAME_FIELDTABLE["IMG_ONE"])
        else: # 이미지가 여럿이면 다수 이미지용 테이블 사용. 단일 이미지용 테이블은 삭제
            self.hwp_control.MoveToField(NAME_FIELDTABLE["TABLE_IMG_ONE_FIRSTCELL"])
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("Delete")  
            self.hwp_control.MoveToField(NAME_FIELDTABLE["IMG_MULTI_FIRST"])
            # 개수 만큼 칸 만들기.
            self.hwp_control.Run("MoveLeft")
            self.hwp_control.HAction.Run("TableCellBlock")
            self.hwp_control.HAction.Run("TableCellBlockExtend")
            self.hwp_control.HAction.Run("TableColPageDown")
            self.hwp_control.HAction.Run("TableColEnd")
            self.hwp_control.HAction.Run("Copy")
            num_expansion = int((num_img - 1) /2)
            for i in range(num_expansion):
                self.hwp_control.HAction.GetDefault("Paste", self.hwp_control.HParameterSet.HSelectionOpt.HSet)
                self.hwp_control.HParameterSet.HSelectionOpt.option = 3
                self.hwp_control.HAction.Execute("Paste", self.hwp_control.HParameterSet.HSelectionOpt.HSet)
            self.hwp_control.MoveToField(NAME_FIELDTABLE["IMG_MULTI_FIRST"])
        
        for idx, path in enumerate(paths_img, start=1):
            text = self._format_evidence_subnumber(path)
            self.hwp_control.InsertPicture(path, Embedded=True, sizeoption=3)
            self.hwp_control.HAction.GetDefault(
                "InsertText", self.hwp_control.HParameterSet.HInsertText.HSet
            )
            self.hwp_control.Run("MoveDown")
            self.hwp_control.HParameterSet.HInsertText.Text = text
            self.hwp_control.HAction.Execute(
                "InsertText", self.hwp_control.HParameterSet.HInsertText.HSet
            )
            if idx==num_img: # 다 채웠으면 메소드 조기 반환
                return
            elif idx % 2 == 1:
                self.hwp_control.Run("MoveRight")
                self.hwp_control.Run("MoveUp")
                self.hwp_control.Run("MoveRight")
            else:
                self.hwp_control.Run("MoveDown")
                self.hwp_control.Run("MoveLeft")
                self.hwp_control.Run("MoveLeft")

    def save_and_move_to_firstpage(self):
        self.hwp_control.Run("MoveDocBegin")
        self.hwp_control.SaveAs(self.path_report)



