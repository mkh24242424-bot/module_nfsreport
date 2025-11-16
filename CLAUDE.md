# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a forensic DNA analysis report generation system for the National Forensic Service (NFS) in South Korea. The system processes STR (Short Tandem Repeat) and Y-STR genetic profile data to automatically generate forensic reports in Korean.

## Commands

### Testing
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests (70 tests total)
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=module --cov-report=term

# Run specific test stages
pytest tests/test_01_main_workflow.py -v              # Stage 1: main.py E2E tests
pytest tests/test_02_features_with_real_data.py -v   # Stage 2: Features with real CSV data
pytest tests/test_03_features_with_inline_data.py -v # Stage 3: Features with inline data
pytest tests/test_04_integration_with_real_data.py -v # Stage 4: Integration with real data
pytest tests/test_05_integration_with_inline_data.py -v # Stage 5: Integration with inline data

# Run a specific test class or method
pytest tests/test_01_main_workflow.py::TestMainWorkflowE2E::test_01_csv_loading -v

# Generate HTML coverage report
pytest tests/ --cov=module --cov-report=html

# Run tests quietly (summary only)
pytest tests/ --tb=no --quiet
```

### Running the Application
```bash
# Activate virtual environment first
source venv/bin/activate

# Run the main script (processes test data)
python main.py

# The script processes CSV files from testdata/ and generates report phrases
```

### Development
```bash
# The project uses a virtual environment
source venv/bin/activate

# Dependencies are managed via pip (no requirements.txt in root currently)
# Main dependencies: pandas, openpyxl, PyQt5, pytest, pytest-cov
```

## Architecture

### Core Modules (module/)

The system follows a **pipeline architecture** that transforms raw profile data into formatted report text:

**1. NFSProfileDataManager** (`NFS_PROFILEDATAMANAGER.py`)
- **Purpose**: Manages collections of genetic profiles and profile-level operations
- **Key responsibilities**:
  - Loads profile data from Tomato Excel files (forensic analysis software output)
  - Manages both STR (24 markers) and Y-STR (20 markers) kits
  - Performs profile comparisons (matching, inclusion relationships)
  - Calculates likelihood ratios using allele frequency data
  - Creates mixed profiles (union of multiple profiles)
- **Important constants**:
  - `DICT_MARKERS`: Ordered lists of genetic markers for STR/YSTR kits
  - `TA_THRESHOLD`: Maximum triallelic loci for mixture determination (2)

**2. STRProfile** (`NFS_STRPROFILE.py`)
- **Purpose**: Represents a single genetic profile
- **Data structure**: `Dict[str, Set[str]]` mapping locus names to allele sets
  - Example: `{"D3S1358": {"15", "16"}, "vWA": {"14", "17"}}`
- **Key methods**:
  - `check_match()`: Determines if two profiles match at common loci
  - `check_inclusion()`: Tests if one profile is contained within another (for mixtures)
  - `union_profiles()`: Creates mixed profile from multiple contributors
  - `export_to_str()`: Formats profile data as Korean report text

**3. NFSReportInformation** (`NFS_REPORTINFORMATION.py`)
- **Purpose**: Central data class aggregating all case information
- **Aggregates**:
  - Case metadata (case ID, requesting agency, dates)
  - Evidence information (DataFrame with evidence items)
  - Profile data managers (STR and Y-STR)
- **Critical**: Acts as the data model passed to NFSReportWriter

**4. NFSReportWriter** (`NFS_REPORTWRITER.py`)
- **Purpose**: Orchestrates report generation from NFSReportInformation
- **Workflow**:
  1. `categorize_profiles()`: Classifies profiles by type (대조/대표/ND/NC)
  2. `make_contents_with_profile()`: Generates phrases for profiles with data
  3. `make_contents_without_profile()`: Generates phrases for ND/NC cases
- **Important**: Uses `switch_kit` property to handle STR/YSTR differences
- **Profile types**:
  - 대조 (Reference): Reference samples for comparison
  - 대표 (Representative): Representative evidence profiles
  - ND (No Data): No DNA detected
  - NC (No Conclusion): Inconclusive results

**5. NFS_REPORTPHRASER** (`NFS_REPORTPHRASER.py`)
- **Purpose**: Pure functions that generate Korean report phrases
- **Key functions**:
  - `make_phrase_ref()`: Reference profile phrases (with likelihood ratios)
  - `make_phrase_res()`: Representative profile phrases
  - `make_phrase_nd()`: No data phrases
  - `make_phrase_nc()`: No conclusion phrases
- **Note**: Uses PyQt5 for GUI dialogs but falls back to terminal input

**6. NFS_DATAFRAME** (`NFS_DATAFRAME.py`)
- **Purpose**: Utility functions for DataFrame processing
- **Key functions**:
  - `xls_to_dataframe()`: Loads Excel files to DataFrames
  - `sort_by_serial_number()`: Natural sort for evidence IDs (e.g., "2023-D-1234-1")
  - `link_num_evidence()`: Groups consecutive evidence items with "~" notation
- **Critical**: `link_num_evidence()` relies on **DataFrame index preservation** to determine evidence continuity

### Data Flow

```
Tomato Excel → NFSProfileDataManager → STRProfile objects
                                              ↓
CSV files → NFSReportInformation ← Profile classifications
                ↓
        NFSReportWriter → NFS_REPORTPHRASER → Korean report text
```

### Key Design Patterns

**1. DataFrame Index Preservation**
- Evidence continuity in reports (e.g., "증1호~증3호") depends on DataFrame row indices
- **Never** use `reset_index(drop=True)` on evidence DataFrames after filtering
- See `extract_evidenceinfo_from_df()` and `link_num_evidence()`

**2. Kit Switching Pattern**
- The `switch_kit` property in NFSReportWriter maps STR/YSTR to their respective variables
- Column names differ by prefix: `대조_이름` (STR) vs `Y_대조_이름` (YSTR)
- This enables code reuse across both kit types

**3. Profile Type Categorization**
- Profiles are categorized into dictionaries: `code_categorized["V"]`, `code_categorized["S"]`, etc.
- Each category processes differently: 대조 profiles get likelihood ratios, ND gets simple phrases

## Testing Strategy

The project uses a **5-stage progressive testing approach** prioritizing main.py workflow validation:

### Test Structure (70 tests total, 100% pass rate)

**Stage 1: main.py E2E Tests** (`test_01_main_workflow.py` - 9 tests)
- Validates the complete workflow from main.py
- Uses real CSV data from `testdata/`
- Tests each step sequentially: CSV loading → ProfileManager → ReportInformation → ReportWriter → Phrase generation
- **Critical**: This stage ensures main.py works correctly end-to-end

**Stage 2: Features with Real Data** (`test_02_features_with_real_data.py` - 17 tests)
- Tests individual module features using real CSV data
- Covers: NFSReportInformation, NFSProfileDataManager, NFSReportWriter, NFS_REPORTPHRASER
- Validates data extraction, profile loading, categorization, phrase generation
- Includes data validation tests (required columns, data types)

**Stage 3: Features with Inline Data** (`test_03_features_with_inline_data.py` - 32 tests)
- Unit tests with data created directly in test code
- Covers: STRProfile, ProfileDataManager, ReportInformation, ReportWriter, Phraser functions, DataFrame utilities
- Tests edge cases: empty data, None values, error handling
- Fast execution, no file I/O dependencies

**Stage 4: Integration with Real Data** (`test_04_integration_with_real_data.py` - 5 tests)
- End-to-end pipelines using real CSV data
- Tests: CSV → ReportInformation → Phrases pipeline, batch processing, STR+YSTR simultaneous processing
- Validates module interactions with realistic data

**Stage 5: Integration with Inline Data** (`test_05_integration_with_inline_data.py` - 7 tests)
- Integration tests with minimal inline data
- Tests: error handling, empty cases, profile filtering, complete integration scenarios
- Validates system behavior with edge cases

### Test Data Files (testdata/)
- `test_df_caseinfo.csv`: Case metadata (접수번호, 의뢰관서, 접수일자, etc.)
- `test_df_report.csv`: Evidence information (감정물번호, 프로필_유형, 코드, etc.)
- `test_df_profile_str.csv`: STR profiles (24 markers)
- `test_df_profile_ystr.csv`: Y-STR profiles (20 markers)

### Key Testing Patterns

**1. User Input Mocking**
Phraser functions may require user input. Use pytest's `monkeypatch`:
```python
def test_phrase_generation(monkeypatch):
    # Mock user input to return 'n' (include identification index)
    monkeypatch.setattr('builtins.input', lambda x: 'n')

    # Now phraser functions won't block waiting for input
    phrase = make_phrase_ref(properties)
```

**2. Common Fixtures (conftest.py)**
- `df_caseinfo`, `df_report`, `df_profile_str`, `df_profile_ystr`: Real CSV data loaded once per session
- `sample_case_id`: Test case ID ("2025-C-6845")
- `assert_equal_with_detail`, `assert_dataframe_equal`: Custom assertions with detailed failure output

**3. Test Failure Output**
When tests fail, conftest.py provides detailed comparison:
```
【예상값 (Expected)】
...expected value...

【실제값 (Actual)】
...actual value...

【차이점 (Difference)】
...highlighted differences...
```

### Important Behavioral Notes

Discovered through testing (actual behavior may differ from expectations):
1. **link_num_evidence()**: Includes empty bodily fluid reactions in output (e.g., "증1호(타액반응 , 정액반응 , 혈흔반응 )")
2. **extract_evidenceinfo_from_df()**: Catches KeyError and prints message instead of raising exception
3. **STRProfile(id=None)**: Stores None as-is, doesn't convert to empty string
4. **make_phrase_ref()**: For victims (피해자), prompts to exclude identification index via user input

## Important Constraints

1. **Logging**: All modules use structured logging. The format is set in `main.py`:
   ```
   [timestamp] [level] [module:function:line] - message
   ```

2. **Korean Language**: All report output, variable names (in DataFrames), and documentation is in Korean

3. **Excel Dependencies**: Production data comes from "Tomato" software (forensic analysis tool) in Excel format

4. **Profile Markers**: The exact order of genetic markers in `DICT_MARKERS` matches the official NFS report format and should not be changed

5. **Allele Frequency**: `allele_frequency.csv` in the module directory is used for likelihood ratio calculations

## Code Organization Principles

- **Single Responsibility**: Each module handles one aspect (profile logic, data management, report writing)
- **Dataclass Usage**: `Properties_Phrase` and `Block_Profile` are dataclasses for structured data passing
- **Type Hints**: Extensive use of typing (Dict, List, Literal, Optional, Self)
- **Logging First**: All significant operations are logged before execution

## Common Patterns

### Creating a Report Workflow
```python
# 1. Load data
pm_str = NFSProfileDataManager(kit="STR")
pm_str.df_profile = pd.read_csv('profiles.csv')

# 2. Create report information
info = NFSReportInformation(id_case='2025-C-6845')
info.extract_caseinfo_from_df(df_caseinfo)
info.extract_evidenceinfo_from_df(df_report)
info.load_str_profiledatamanager(pm_str)

# 3. Generate report
RW = NFSReportWriter(info, [])
RW.categorize_profiles()
RW.make_contents_with_profile(phraser=make_phrase_ref, type_profile='대조')
```

### Working with STRProfile
```python
# Create profile
profile = STRProfile(id="A", profile={"D3S1358": {"15", "16"}})

# Check match
matches = profile.check_match(other_profile)

# Create mixture
mixed = profile.union_profiles(other_profile)
```

## Current Development Status

- **Branch**: `refactor/create-text-evidence` (active refactoring branch)
- **Recent work**: Complete test suite rewrite with 5-stage progressive testing
- **Modified files**: `main.py`, `NFS_REPORTWRITER.py`
- **Test suite**: 70 tests across 5 test files (100% pass rate)
  - Comprehensive coverage of main.py workflow
  - Real data validation with testdata/ CSV files
  - Unit tests for all core modules
  - Integration tests for module interactions
  - Edge case and error handling tests
