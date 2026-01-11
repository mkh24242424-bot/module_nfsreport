# CLAUDE.md

이 파일은 Claude Code가 프로젝트를 이해하는 데 도움을 주는 설정 파일입니다.

## 프로젝트 개요

국립과학수사연구원(NFS) DNA 감정서 자동 생성 모듈입니다. CSV 데이터를 기반으로 STR/Y-STR DNA 프로필 분석 결과를 HWP(한글) 형식의 감정서로 자동 생성합니다.

## 프로젝트 구조

```
module_nfsreport/
├── main.py                 # 메인 실행 파일
├── module/                 # 핵심 모듈 디렉토리
│   ├── NFS_BLOCKMANAGER.py      # 프로필 블록 관리
│   ├── NFS_DATAFRAME.py         # 데이터프레임 유틸리티
│   ├── NFS_HWPFORMATTER.py      # HWP 파일 생성/편집
│   ├── NFS_PROFILEDATAMANAGER.py # DNA 프로필 데이터 관리
│   ├── NFS_REPORTINFORMATION.py  # 보고서 정보 관리
│   ├── NFS_REPORTPHRASER.py     # 보고서 문구 생성
│   ├── NFS_REPORTWRITER.py      # 보고서 작성
│   ├── NFS_STRPROFILE.py        # STR 프로필 처리
│   ├── likelihood_calculator.py  # 우도비 계산
│   ├── exceptions.py            # 예외 클래스
│   └── constants_*.py           # 상수 정의 파일들
├── form/                   # HWP 템플릿 파일
├── testdata/               # 테스트용 CSV 데이터
├── img/                    # 이미지 리소스
└── report/                 # 생성된 보고서 출력
```

## 실행 방법

```bash
python main.py
```

## 의존성

- Python 3.x
- pandas
- pyhwpx (HWP 파일 처리)

## 주요 워크플로우

1. CSV 파일에서 사건 정보, 증거물 정보, DNA 프로필 데이터 로드
2. `NFSReportInformation`으로 사건/증거물 정보 추출
3. `NFSProfileDataManager`로 STR/Y-STR 프로필 데이터 관리
4. `BlockProfileManager`로 프로필 블록 생성
5. `NFSReportWriter`로 보고서 내용 작성
6. `NFS_HWPFormatter`로 HWP 감정서 생성

## 코딩 컨벤션

- 클래스명: `NFS_` 접두사 사용 (예: `NFS_HWPFormatter`)
- 상수 파일: `constants_*.py` 형식
- 로깅: `logging` 모듈 사용, DEBUG 레벨 지원
- 언어: 한국어 주석 및 변수명 혼용

## 주의사항

- HWP 파일 처리는 Windows 환경에서만 정상 동작 (pyhwpx 의존성)
- DNA 프로필 데이터는 민감 정보이므로 테스트 데이터만 커밋
- allele 값의 `*` 문자는 위첨자로 출력됨
