# 테스트 데이터 전략 가이드

## 📊 현재 상황 분석

### 사용한 방식
✅ **모든 테스트에서 인라인 데이터 생성**
- 91개 테스트 모두 `pd.DataFrame()`, `STRProfile()` 등으로 데이터 직접 생성
- `tempfile`을 사용한 임시 파일 생성
- testdata/ 디렉토리의 실제 데이터는 미사용

### 사용 가능한 실제 데이터
```
testdata/
├── test_df_caseinfo.csv         (124KB, 사건정보)
├── test_df_profile_str.csv      (22KB, STR 프로파일)
├── test_df_profile_ystr.csv     (9.5KB, Y-STR 프로파일)
└── test_df_report.csv           (36KB, 리포트 데이터)
```

---

## 🎯 두 가지 접근법 비교

### 방법 1: 인라인 데이터 생성 (현재 방식)

#### 예시
```python
def test_check_match(self):
    """특정 시나리오만 집중 테스트"""
    profile1 = STRProfile(id="A", profile={
        "D3S1358": {"15", "16"},
        "vWA": {"14", "17"}
    })
    profile2 = STRProfile(id="B", profile={
        "D3S1358": {"15", "16"},
        "vWA": {"14", "17"}
    })

    assert profile1.check_match(profile2) is True
```

#### 장점 ✅
- **명확성**: 테스트 의도가 명확히 드러남
- **독립성**: 다른 파일/데이터에 의존하지 않음
- **간결성**: 필요한 최소 데이터만 사용
- **속도**: 데이터 로딩 오버헤드 없음
- **유지보수**: 테스트 코드만 보면 완전히 이해 가능

#### 단점 ❌
- **반복**: 비슷한 구조를 여러 번 작성
- **현실성 부족**: 실제 데이터의 복잡성 반영 안 됨
- **리소스 낭비**: 준비된 testdata 미활용

#### 적합한 경우 ✨
- **단위 테스트**: 특정 메서드/기능만 검증
- **엣지 케이스**: 빈 데이터, None, 예외 상황
- **경계값 테스트**: 최소/최대값, 특수 케이스
- **빠른 피드백 필요**: 개발 중 빈번한 테스트

---

### 방법 2: 실제 데이터 활용 (개선 방안)

#### 예시
```python
@pytest.fixture
def df_caseinfo():
    """실제 사건정보 데이터 로드"""
    return pd.read_csv("testdata/test_df_caseinfo.csv")

def test_with_real_data(df_caseinfo):
    """실제 데이터로 통합 검증"""
    first_case = df_caseinfo.iloc[0]['접수번호']

    report_info = NFSReportInformation(id_case=first_case)
    report_info.extract_caseinfo_from_df(df_caseinfo)

    # 실제 데이터 구조로 동작 확인
    assert '의뢰관서' in report_info.caseinfo
```

#### 장점 ✅
- **현실성**: 실제 운영 데이터와 유사한 환경
- **통합성**: 여러 모듈 간 상호작용 검증
- **데이터 품질**: 실제 데이터의 이슈 발견 가능
- **회귀 방지**: 기존 동작 유지 확인

#### 단점 ❌
- **복잡성**: 데이터 구조 이해 필요
- **유지보수**: 데이터 변경 시 테스트 영향
- **속도**: 파일 I/O 오버헤드
- **디버깅**: 실패 원인 파악 어려움

#### 적합한 경우 ✨
- **통합 테스트**: 여러 모듈이 함께 동작
- **회귀 테스트**: 기존 기능 유지 확인
- **성능 테스트**: 대용량 데이터 처리
- **데이터 검증**: 실제 데이터 품질 확인

---

## 🎨 권장 테스트 전략: 피라미드 구조

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲         1-2개: 실제 데이터 + 전체 워크플로우
                 ╱______╲
                ╱        ╲
               ╱ 통합테스트 ╲      10-15개: 실제 데이터 + 모듈 조합
              ╱____________╲
             ╱              ╲
            ╱   단위 테스트    ╲    70-80개: 인라인 데이터 + 개별 기능
           ╱__________________╲
```

### 1. 단위 테스트 (70-80%) - 인라인 데이터
**목적**: 개별 함수/메서드의 정확성 검증

```python
# ✅ GOOD: 명확하고 간결한 단위 테스트
def test_check_match_identical_profiles(self):
    profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
    profile2 = STRProfile(id="B", profile={"D3S1358": {"15", "16"}})
    assert profile1.check_match(profile2) is True

def test_check_match_different_profiles(self):
    profile1 = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})
    profile2 = STRProfile(id="B", profile={"D3S1358": {"17", "18"}})
    assert profile1.check_match(profile2) is False
```

### 2. 통합 테스트 (10-15%) - 실제 데이터
**목적**: 모듈 간 상호작용 및 데이터 흐름 검증

```python
# ✅ GOOD: 실제 데이터로 통합 시나리오 검증
@pytest.fixture
def real_case_data():
    return {
        'caseinfo': pd.read_csv("testdata/test_df_caseinfo.csv"),
        'profiles': pd.read_csv("testdata/test_df_profile_str.csv")
    }

def test_full_report_generation(real_case_data):
    """실제 데이터로 전체 리포트 생성 프로세스 테스트"""
    case_id = real_case_data['caseinfo'].iloc[0]['접수번호']

    # 1. 정보 추출
    report_info = NFSReportInformation(id_case=case_id)
    report_info.extract_caseinfo_from_df(real_case_data['caseinfo'])

    # 2. 프로파일 로드
    pdm = NFSProfileDataManager(kit="STR")
    pdm.df_profile = real_case_data['profiles']
    report_info.load_str_profiledatamanager(pdm)

    # 3. 동작 검증
    assert report_info.caseinfo is not None
    assert report_info.pm_str is not None
```

### 3. E2E 테스트 (1-2%) - 실제 데이터 + 전체 워크플로우
**목적**: 사용자 시나리오 전체 검증

```python
def test_complete_workflow_from_tomato_to_report():
    """토마토 파일부터 감정서 생성까지 전체 워크플로우"""
    # 실제 사용 시나리오 재현
    pass
```

---

## 📝 실제 적용 예시

### 기존 테스트 (91개)
모두 **단위 테스트 + 인라인 데이터** ✅

### 추가 권장 테스트

#### 1. 통합 테스트 추가 (생성 완료)
**파일**: `tests/test_with_real_data.py`

```python
# 실제 데이터 활용 테스트 6개 추가
- test_extract_caseinfo_from_real_data
- test_real_data_structure
- test_profiledatamanager_with_real_data
- test_data_consistency
- test_no_missing_critical_fields
- test_data_types
```

**결과**: ✅ 6/6 통과

#### 2. 데이터 품질 테스트
```python
def test_data_completeness(df_caseinfo):
    """필수 필드 완전성 검증"""
    required_fields = ['접수번호', '의뢰관서', '접수일자', '시행일자']
    for field in required_fields:
        assert field in df_caseinfo.columns
        null_ratio = df_caseinfo[field].isna().sum() / len(df_caseinfo)
        assert null_ratio < 0.1, f"{field}의 null 비율이 {null_ratio:.1%}로 높음"
```

#### 3. 성능 테스트 (향후)
```python
@pytest.mark.performance
def test_large_dataset_performance(df_profile_str):
    """대용량 데이터 처리 성능"""
    import time

    start = time.time()
    pdm = NFSProfileDataManager(kit="STR")
    pdm.df_profile = df_profile_str
    # 대량 처리 작업...
    elapsed = time.time() - start

    assert elapsed < 5.0, f"처리 시간 {elapsed:.2f}초, 목표 5초 초과"
```

---

## 🔧 pytest fixtures 활용

### 공통 테스트 데이터 fixtures

**파일**: `tests/conftest.py` (생성 권장)

```python
import pytest
import pandas as pd
from pathlib import Path

# 테스트 데이터 경로
TESTDATA_DIR = Path(__file__).parent.parent / "testdata"


# 레벨 1: 파일 레벨 fixtures (모든 테스트에서 공유)
@pytest.fixture(scope="session")
def df_caseinfo_full():
    """전체 사건정보 데이터 (세션 동안 한 번만 로드)"""
    return pd.read_csv(TESTDATA_DIR / "test_df_caseinfo.csv")


@pytest.fixture(scope="session")
def df_profile_str_full():
    """전체 STR 프로파일 데이터"""
    return pd.read_csv(TESTDATA_DIR / "test_df_profile_str.csv")


# 레벨 2: 함수 레벨 fixtures (각 테스트마다 새로운 복사본)
@pytest.fixture
def sample_case_id(df_caseinfo_full):
    """테스트용 샘플 사건번호"""
    return df_caseinfo_full.iloc[0]['접수번호']


@pytest.fixture
def sample_caseinfo(df_caseinfo_full):
    """테스트용 샘플 사건정보 (수정 가능한 복사본)"""
    return df_caseinfo_full.head(5).copy()


# 레벨 3: 파라미터화된 fixtures
@pytest.fixture(params=["STR", "YSTR"])
def kit_type(request):
    """STR과 YSTR 모두 테스트"""
    return request.param
```

### fixtures 사용 예시

```python
def test_with_fixtures(sample_case_id, sample_caseinfo):
    """fixtures를 활용한 간결한 테스트"""
    report_info = NFSReportInformation(id_case=sample_case_id)
    report_info.extract_caseinfo_from_df(sample_caseinfo)

    assert report_info.caseinfo['의뢰관서'] is not None


@pytest.mark.parametrize("kit", ["STR", "YSTR"])
def test_multiple_kits(kit):
    """파라미터화로 여러 키트 테스트"""
    pdm = NFSProfileDataManager(kit=kit)
    assert pdm.kit == kit
```

---

## 📊 현재 vs 개선된 테스트 구조

### 현재 구조
```
tests/
├── test_nfs_strprofile.py         (27개, 단위)
├── test_nfs_dataframe.py          (18개, 단위)
├── test_nfs_reportinformation.py  (11개, 단위)
├── test_nfs_profiledatamanager.py (26개, 단위)
└── test_nfs_reportwriter.py       (9개, 단위)

총 91개, 모두 인라인 데이터
```

### 개선된 구조
```
tests/
├── conftest.py                     (공통 fixtures)
│
├── unit/                           (단위 테스트, 인라인 데이터)
│   ├── test_nfs_strprofile.py     (27개)
│   ├── test_nfs_dataframe.py      (18개)
│   ├── test_nfs_reportinformation.py (11개)
│   ├── test_nfs_profiledatamanager.py (26개)
│   └── test_nfs_reportwriter.py   (9개)
│
├── integration/                    (통합 테스트, 실제 데이터)
│   ├── test_with_real_data.py     (6개) ✅ 생성 완료
│   ├── test_data_quality.py       (추가 권장)
│   └── test_module_integration.py (추가 권장)
│
└── e2e/                            (E2E 테스트, 전체 워크플로우)
    └── test_complete_workflow.py  (추가 권장)

총 97+ 개, 피라미드 구조
```

---

## 🎯 결론 및 권장사항

### 현재 상황 평가
✅ **잘한 점**:
- 91개의 견고한 단위 테스트 작성
- 100% 통과율
- 핵심 모듈 높은 커버리지

❓ **개선 가능한 점**:
- 실제 데이터로 통합 테스트 부족
- 모듈 간 상호작용 검증 부족
- testdata/ 리소스 미활용

### 권장 액션 아이템

#### 즉시 (1주일)
1. ✅ `tests/test_with_real_data.py` 생성 완료
2. ⬜ `tests/conftest.py` 생성 - 공통 fixtures
3. ⬜ 기존 테스트 중 2-3개를 실제 데이터 버전으로 추가

#### 단기 (1개월)
4. ⬜ 통합 테스트 10개 추가
5. ⬜ 데이터 품질 테스트 추가
6. ⬜ 테스트 디렉토리 재구성 (unit/integration 분리)

#### 중기 (3개월)
7. ⬜ E2E 테스트 작성
8. ⬜ 성능 테스트 추가
9. ⬜ CI/CD 파이프라인 구축

---

## 💡 베스트 프랙티스

### DO ✅
- 단위 테스트는 인라인 데이터로 간결하게
- 통합 테스트는 실제 데이터로 현실적으로
- fixtures로 중복 제거
- 테스트 이름으로 의도 명확히 표현

### DON'T ❌
- 모든 테스트를 실제 데이터로 작성하지 말 것
- 테스트 간 데이터 공유로 의존성 만들지 말 것
- 너무 복잡한 테스트 데이터 생성하지 말 것
- 테스트 실패 시 원인 찾기 어렵게 만들지 말 것

---

**작성**: 2025-11-11
**버전**: 1.0
