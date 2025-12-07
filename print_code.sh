#!/bin/bash
# 코드 프린트용 스크립트
# 사용법: ./print_code.sh [옵션]
# 옵션: module (모듈만), tests (테스트만), all (전체, 기본값)

set -e

PRINT_TARGET="${1:-all}"
OUTPUT_DIR="printable_code"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

echo "📄 코드 프린트 준비 시작..."
echo "대상: $PRINT_TARGET"
echo ""

# =============================================================================
# 옵션 1: enscript 사용 (2-column, 라인번호, 신택스 하이라이팅)
# =============================================================================
generate_with_enscript() {
    echo "=== enscript로 PostScript 생성 ==="

    if ! command -v enscript &> /dev/null; then
        echo "⚠️  enscript가 설치되지 않았습니다."
        echo "설치: sudo apt-get install enscript"
        return 1
    fi

    local files=("$@")
    local output="${OUTPUT_DIR}/code_enscript_${TIMESTAMP}.ps"

    enscript \
        --language=python \
        --color \
        --columns=2 \
        --landscape \
        --line-numbers \
        --mark-wrapped-lines=arrow \
        --header='$n|코드 리뷰|페이지 $% / $=' \
        --fancy-header=fancy \
        --font=Courier8 \
        --output="$output" \
        "${files[@]}"

    echo "✅ PostScript 파일 생성: $output"
    echo "   PDF 변환: ps2pdf $output ${output%.ps}.pdf"

    if command -v ps2pdf &> /dev/null; then
        ps2pdf "$output" "${output%.ps}.pdf"
        echo "✅ PDF 파일 생성: ${output%.ps}.pdf"
    fi
}

# =============================================================================
# 옵션 2: pygmentize 사용 (HTML → PDF, 아름다운 신택스 하이라이팅)
# =============================================================================
generate_with_pygmentize() {
    echo "=== pygmentize로 HTML 생성 ==="

    if ! command -v pygmentize &> /dev/null; then
        echo "⚠️  pygmentize가 설치되지 않았습니다."
        echo "설치: pip install pygments"
        return 1
    fi

    local files=("$@")
    local output="${OUTPUT_DIR}/code_pygments_${TIMESTAMP}.html"

    cat > "$output" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NFS Report 코드</title>
    <style>
        @media print {
            body { font-size: 9pt; }
            pre { page-break-inside: avoid; }
            .file-header { page-break-before: always; }
            .file-header:first-of-type { page-break-before: auto; }
        }
        body {
            font-family: 'Consolas', 'Monaco', monospace;
            max-width: 1200px;
            margin: 20px auto;
        }
        .file-header {
            background: #2c3e50;
            color: white;
            padding: 10px;
            margin-top: 20px;
            border-radius: 5px;
        }
        .line-numbers {
            background: #f5f5f5;
            border-radius: 5px;
            padding: 10px;
        }
        .toc {
            background: #ecf0f1;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .toc h2 { margin-top: 0; }
        .toc ul { list-style: none; padding-left: 0; }
        .toc li { padding: 5px 0; }
    </style>
</head>
<body>
<h1>NFS Report System - 코드 문서</h1>
<p>생성 시각: $(date '+%Y년 %m월 %d일 %H:%M:%S')</p>

<div class="toc">
<h2>📑 목차</h2>
<h3>모듈 파일</h3>
<ul>
<li>main.py (엔트리 포인트)</li>
<li>module/NFS_DATAFRAME.py (151 lines) - 데이터프레임 유틸리티</li>
<li>module/NFS_PROFILEDATAMANAGER.py (992 lines) - 프로필 데이터 관리 (Facade + 5개 전문 클래스)</li>
<li>module/NFS_REPORTINFORMATION.py (56 lines) - 보고서 정보 모델</li>
<li>module/NFS_REPORTPHRASER.py (277 lines) - 문구 생성기</li>
<li>module/NFS_REPORTWRITER.py (657 lines) - 보고서 작성기 (Facade + 3개 전문 클래스)</li>
<li>module/NFS_STRPROFILE.py (241 lines) - STR 프로필 모델</li>
<li>module/exceptions.py (117 lines) - 커스텀 예외</li>
</ul>
</div>

EOF

    for file in "${files[@]}"; do
        echo "<div class='file-header'>" >> "$output"
        echo "<h2>📄 $file ($(wc -l < "$file") lines)</h2>" >> "$output"
        echo "</div>" >> "$output"

        pygmentize -f html -O style=monokai,linenos=inline,cssclass=line-numbers "$file" >> "$output"
        echo "<hr style='margin: 40px 0; border: none; border-top: 2px dashed #ccc;'>" >> "$output"
    done

    echo "</body></html>" >> "$output"

    echo "✅ HTML 파일 생성: $output"
    echo "   브라우저에서 열어 Ctrl+P로 PDF 저장하세요."

    # wkhtmltopdf가 있으면 자동 PDF 변환
    if command -v wkhtmltopdf &> /dev/null; then
        wkhtmltopdf --enable-local-file-access "$output" "${output%.html}.pdf"
        echo "✅ PDF 파일 생성: ${output%.html}.pdf"
    fi
}

# =============================================================================
# 옵션 3: 간단한 텍스트 파일 (라인 번호 포함)
# =============================================================================
generate_simple_text() {
    echo "=== 간단한 텍스트 파일 생성 ==="

    local files=("$@")
    local output="${OUTPUT_DIR}/code_simple_${TIMESTAMP}.txt"

    cat > "$output" << EOF
================================================================================
NFS Report System - 코드 리스트
생성 시각: $(date '+%Y년 %m월 %d일 %H:%M:%S')
================================================================================

목차:
$(for f in "${files[@]}"; do echo "  - $f ($(wc -l < "$f") lines)"; done)

================================================================================

EOF

    for file in "${files[@]}"; do
        echo "" >> "$output"
        echo "################################################################################" >> "$output"
        echo "# 파일: $file" >> "$output"
        echo "# 라인 수: $(wc -l < "$file")" >> "$output"
        echo "################################################################################" >> "$output"
        echo "" >> "$output"

        # 라인 번호 추가
        cat -n "$file" >> "$output"

        echo "" >> "$output"
        echo "" >> "$output"
    done

    echo "✅ 텍스트 파일 생성: $output"
}

# =============================================================================
# 파일 목록 준비
# =============================================================================
MODULE_FILES=(
    "main.py"
    "module/NFS_DATAFRAME.py"
    "module/NFS_STRPROFILE.py"
    "module/exceptions.py"
    "module/NFS_REPORTINFORMATION.py"
    "module/NFS_PROFILEDATAMANAGER.py"
    "module/NFS_REPORTWRITER.py"
    "module/NFS_REPORTPHRASER.py"
)

TEST_FILES=(
    "tests/conftest.py"
    "tests/test_01_main_workflow.py"
    "tests/test_02_features_with_real_data.py"
    "tests/test_03_features_with_inline_data.py"
    "tests/test_04_integration_with_real_data.py"
    "tests/test_05_integration_with_inline_data.py"
    "tests/test_06_phase4_profilemanager_classes.py"
    "tests/test_07_reportphraser_coverage.py"
    "tests/test_08_reportwriter_edge_cases.py"
)

# =============================================================================
# 실행
# =============================================================================
case "$PRINT_TARGET" in
    module)
        echo "📦 모듈 파일만 처리 (2,491 lines)"
        FILES=("${MODULE_FILES[@]}")
        ;;
    tests)
        echo "🧪 테스트 파일만 처리 (3,191 lines)"
        FILES=("${TEST_FILES[@]}")
        ;;
    all|*)
        echo "📚 전체 파일 처리 (5,764 lines)"
        FILES=("${MODULE_FILES[@]}" "${TEST_FILES[@]}")
        ;;
esac

echo ""
echo "처리 파일 수: ${#FILES[@]}"
echo ""

# 모든 방법으로 생성 시도
generate_simple_text "${FILES[@]}"
echo ""
generate_with_pygmentize "${FILES[@]}"
echo ""
generate_with_enscript "${FILES[@]}"

echo ""
echo "========================================="
echo "✅ 완료! 결과물:"
echo "========================================="
ls -lh "$OUTPUT_DIR"/*${TIMESTAMP}*
echo ""
echo "💡 프린트 팁:"
echo "   1. HTML/PDF: 컬러 프린터 추천"
echo "   2. 양면 인쇄 활성화"
echo "   3. 용지 크기: A4"
echo "   4. 여백: 최소 (1cm)"
echo ""
