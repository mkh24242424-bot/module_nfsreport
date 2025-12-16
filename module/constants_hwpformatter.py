from dataclasses import dataclass   

PATH_HWP_TEMPLATE ={
    "DEFAULT": "/form/form_report_default.hwp",
    # Future report type forms can be added here
    # "suspect": "path/to/suspect_form.hwp",
    # "paternity": "path/to/paternity_form.hwp",
}

NAME_FIELDTEXT ={
    "의뢰관서": "goansuname",
    "문서번호": "munsuno",
    "접수일자": "jubsudate",
    "시행일자": "sihangdate",
    "접수번호": "jubsuno",
    "감정물": "gamjungmul",
    "실험방법": "experiment_method",
    "실험결과": "phrase_result",
    "기타": "remark",
    "소속": "position",
    "STR프로필_기타":"STR_ETC",
    "YSTR프로필_기타":"YSTR_ETC",

}

NAME_FIELDTABLE = {
    "TABLE_STR_FIRSTCELL": "TABLE_STR_FIRSTCELL",
    "STR_FIRSTCOL": "STR_FIRSTCOL",
    "TABLE_YSTR_FIRSTCELL": "TABLE_YSTR_FIRSTCELL",
    "YSTR_FIRSTCOL":"YSTR_FIRSTCOL",
    "TABLE_IMG_MULTI_FIRSTCELL":"TABLE_IMG_MULTI_FIRSTCELL",
    "IMG_MULTI_FIRST":"IMG_MULTI_FIRST",
    "TABLE_IMG_ONE_FIRSTCELL":"TABLE_IMG_ONE_FIRSTCELL",
    "IMG_ONE":"IMG_ONE"
}

# 도장 관련 데이터클래스
@dataclass
class SealField:
    field_name: str
    field_img: str

LIST_SEALFIELD= [
    SealField(field_name="#이름4", field_img="#도장4"),
    SealField(field_name="#이름5", field_img="#도장5"),
    SealField(field_name="#이름6", field_img="#도장6"),
]

KEYWORDS_PAIREDPROFILE = ["상피세포층", "정자층", "검출형", "추정형"]