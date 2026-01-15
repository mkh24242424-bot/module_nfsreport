"""
Postprocessor module for NFSReport.

감정서 작성 후 특이 조건에 대한 후처리를 담당합니다.
"""


from module.constants_hwpformatter import NAME_FIELDTABLE


class TextPostprocessor:
    """텍스트 레벨 후처리"""

    def process_evidence(self, text: str) -> str:
        """
        증거물명 텍스트 변환.

        변환 규칙:
        - "담배꽁초" → "담배꽁초()"
        """
        result = text
        result = result.replace("담배꽁초", "담배꽁초()")
        return result


class HWPPostprocessor:
    """HWP 레벨 후처리 - HWP 파일 내 텍스트 스캔 및 형식 변경"""

    def __init__(self, hwp_control):
        self.hwp_control = hwp_control

    def process(self) -> None:
        flag_ystr_table = False # 해당 문구가 없으면 표를 삭제 
        flag_db_table = False # 해당 문구가 없으면 표를 삭제
        self.hwp_control.InitScan()
        while True:
            state, text = self.hwp_control.GetText()
            # 식별 지수 문구의 10^ 부분에 대해 위첨자로 변경
            # 예시: 이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서 {info.likelihoodratio[0]} x 10{info.likelihoodratio[1]}임.\r\n"
            if "이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서" in text:
                self.hwp_control.MovePos(201) # 해당 문구 처음으로 이동
                self.hwp_control.Run("MoveLineEnd") # 문구 끝으로 이동
                self.hwp_control.Run("MoveLeft") # 위첨자 적용 위치로 이동
                self.hwp_control.Run("MoveLeft")
                self.hwp_control.Run("MoveLeft")
                self.hwp_control.Run("MoveLeft")
                self.hwp_control.Run("MoveSelRight") # 적용 범위 선택
                self.hwp_control.Run("MoveSelRight")
                self.hwp_control.Run("CharShapeSuperscript")
                self.hwp_control.Run("Cancel")
            if "Y-STR 유전자형 분석법(NFS-QI-DAM-03:2020)" in text:
                flag_ystr_table = True
            if "다음 [표]의 사건에서 확보된 디엔에이형과 일치" in text:
                flag_db_table = True
            if state <= 1:
                break
        self.hwp_control.ReleaseScan()
        if not flag_ystr_table:
            print("YSTR 표 삭제")
            self.hwp_control.MoveToField(NAME_FIELDTABLE["TABLE_YSTR_FIRSTCELL"])
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("Delete")
        if not flag_db_table:  
            self.hwp_control.MoveToField(NAME_FIELDTABLE["TABLE_DB_FIRSTCELL"])
            self.hwp_control.HAction.Run("SelectCtrlReverse")
            self.hwp_control.HAction.Run("Delete")
        self.hwp_control.Run("MoveDocBegin")
        self.hwp_control.MovePos(2) # 캐럿을 문서 처음으로 이동


            