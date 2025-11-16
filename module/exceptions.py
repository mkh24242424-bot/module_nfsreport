"""
커스텀 예외 클래스 정의

NFS 리포트 생성 시스템에서 사용되는 도메인 특화 예외들을 정의합니다.
표준 예외 클래스를 사용하는 것보다 명확한 의미 전달과 에러 처리가 가능합니다.
"""


class NFSReportError(Exception):
    """NFS 리포트 시스템의 기본 예외 클래스

    모든 커스텀 예외는 이 클래스를 상속받습니다.
    """
    pass


class CaseNotFoundError(NFSReportError):
    """사건 정보를 찾을 수 없을 때 발생하는 예외

    데이터프레임에서 특정 사건 ID(접수번호)를 찾을 수 없을 때 발생합니다.

    Attributes:
        case_id: 찾으려던 사건 ID
        message: 에러 메시지
    """

    def __init__(self, case_id: str, message: str = None):
        self.case_id = case_id
        self.message = message or f"사건 정보를 찾을 수 없습니다: {case_id}"
        super().__init__(self.message)


class EvidenceNotFoundError(NFSReportError):
    """증거물 정보를 찾을 수 없을 때 발생하는 예외

    데이터프레임에서 특정 증거물 코드를 찾을 수 없을 때 발생합니다.

    Attributes:
        evidence_code: 찾으려던 증거물 코드
        message: 에러 메시지
    """

    def __init__(self, evidence_code: str, message: str = None):
        self.evidence_code = evidence_code
        self.message = message or f"증거물 정보를 찾을 수 없습니다: {evidence_code}"
        super().__init__(self.message)


class ProfileNotFoundError(NFSReportError):
    """프로필 정보를 찾을 수 없을 때 발생하는 예외

    프로필 매니저에서 특정 프로필을 찾을 수 없을 때 발생합니다.

    Attributes:
        profile_id: 찾으려던 프로필 ID
        message: 에러 메시지
    """

    def __init__(self, profile_id: str, message: str = None):
        self.profile_id = profile_id
        self.message = message or f"프로필을 찾을 수 없습니다: {profile_id}"
        super().__init__(self.message)


class InvalidDataError(NFSReportError):
    """데이터가 유효하지 않을 때 발생하는 예외

    데이터 검증 실패, 필수 컬럼 누락, 잘못된 데이터 형식 등의 경우 발생합니다.

    Attributes:
        data_type: 데이터 유형 (예: "DataFrame", "Profile")
        message: 에러 메시지
    """

    def __init__(self, data_type: str, message: str):
        self.data_type = data_type
        self.message = f"[{data_type}] {message}"
        super().__init__(self.message)


class TemplateError(NFSReportError):
    """감정서 문구 템플릿 오류 시 발생하는 예외

    Phraser 함수 호출 시 잘못된 파라미터나 템플릿 오류가 발생할 때 사용합니다.

    Attributes:
        template_name: 템플릿/함수 이름
        original_error: 원래 발생한 에러
        message: 에러 메시지
    """

    def __init__(self, template_name: str, original_error: Exception = None):
        self.template_name = template_name
        self.original_error = original_error

        if original_error:
            self.message = f"감정서 문구 템플릿 오류 [{template_name}]: {str(original_error)}"
        else:
            self.message = f"감정서 문구 템플릿 오류: {template_name}"

        super().__init__(self.message)


class DataFrameOperationError(NFSReportError):
    """DataFrame 작업 중 오류 발생 시 사용하는 예외

    그룹바이, 필터링, 병합 등의 DataFrame 작업 실패 시 발생합니다.

    Attributes:
        operation: 작업 유형
        message: 에러 메시지
    """

    def __init__(self, operation: str, message: str):
        self.operation = operation
        self.message = f"DataFrame {operation} 작업 실패: {message}"
        super().__init__(self.message)
