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