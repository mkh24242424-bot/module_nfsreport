#!/usr/bin/env python3
"""
코드 HTML 생성 스크립트 (개선된 버전 - Light Theme)

module 디렉토리의 Python 파일들을 읽어서 전문 에디터 스타일의 syntax highlighting이 적용된 HTML로 변환합니다.
VS Code Light+ 테마를 기반으로 한 컬러 팔레트를 사용합니다. (인쇄 친화적)
"""

import os
from pathlib import Path
from datetime import datetime

try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    print("⚠️  pygments not found. Using basic syntax highlighting.")

# VS Code Dark+ 스타일 HTML 템플릿
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFS Report Module - Source Code</title>
    <style>
        @media print {{
            .file-section {{
                page-break-before: always;
            }}
            .file-section:first-child {{
                page-break-before: avoid;
            }}
            body {{
                background: white !important;
            }}
            .header {{
                background: #667eea !important;
                color: white !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .copy-button {{
                display: none; /* 인쇄 시 복사 버튼 숨김 */
            }}
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', 'Menlo', monospace;
            line-height: 1.6;
            background: #f5f5f5;
            color: #333333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            margin: 0 0 15px 0;
            font-size: 32px;
            font-weight: 600;
        }}

        .header .meta {{
            opacity: 0.95;
            font-size: 15px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

        .toc {{
            background: #ffffff;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .toc h2 {{
            margin: 0 0 20px 0;
            color: #0066cc;
            font-size: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}

        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}

        .toc li {{
            padding: 10px 15px;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s;
        }}

        .toc li:last-child {{
            border-bottom: none;
        }}

        .toc li:hover {{
            background: #f8f8f8;
        }}

        .toc a {{
            color: #0066cc;
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            font-size: 14px;
        }}

        .toc a:hover {{
            color: #0052a3;
        }}

        .toc .file-name {{
            font-weight: 500;
        }}

        .toc .line-count {{
            color: #666666;
            font-size: 13px;
        }}

        .file-section {{
            background: #ffffff;
            margin-bottom: 30px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .file-header {{
            background: #f8f9fa;
            color: #333333;
            padding: 18px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e0e0e0;
            position: relative;
        }}

        .file-header h2 {{
            margin: 0;
            font-size: 16px;
            font-weight: 500;
            color: #0066cc;
        }}

        .file-meta {{
            font-size: 12px;
            color: #666666;
            font-family: 'Segoe UI', sans-serif;
        }}

        .code-container {{
            background: #ffffff;
            overflow-x: auto;
        }}

        pre {{
            margin: 0;
            padding: 20px;
            font-size: 14px;
            line-height: 1.8;
            overflow-x: auto;
        }}

        code {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}

        /* 라인 호버 효과 */
        .highlight table tr:hover {{
            background-color: #f0f7ff;
        }}

        /* 코드 복사 버튼 */
        .copy-button {{
            position: absolute;
            right: 10px;
            top: 10px;
            padding: 6px 12px;
            background: #ffffff;
            color: #333333;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-family: 'Segoe UI', sans-serif;
            transition: all 0.2s;
        }}

        .copy-button:hover {{
            background: #f0f0f0;
            border-color: #999999;
        }}

        .copy-button:active {{
            background: #e0e0e0;
        }}

        .copy-button.copied {{
            background: #0066cc;
            color: #ffffff;
            border-color: #0066cc;
        }}

        /* Pygments 스타일 (VS Code Light+ 기반) */
        .highlight {{
            background: #ffffff;
        }}

        .highlight .hll {{ background-color: #ffffcc; }} /* 하이라이트 라인 */
        .highlight .c {{ color: #008000; font-style: italic; }} /* Comment - 녹색 */
        .highlight .err {{ color: #ff0000; background-color: #ffcccc; }} /* Error - 빨간색 */
        .highlight .k {{ color: #0000ff; font-weight: 500; }} /* Keyword - 파란색 강조 */
        .highlight .l {{ color: #098658; }} /* Literal */
        .highlight .n {{ color: #001080; }} /* Name - 진한 파란색 */
        .highlight .o {{ color: #000000; }} /* Operator - 검은색 */
        .highlight .p {{ color: #000000; }} /* Punctuation - 검은색 */
        .highlight .ch {{ color: #008000; font-style: italic; }} /* Comment.Hashbang */
        .highlight .cm {{ color: #008000; font-style: italic; }} /* Comment.Multiline */
        .highlight .cp {{ color: #0000ff; }} /* Comment.Preproc */
        .highlight .cpf {{ color: #008000; font-style: italic; }} /* Comment.PreprocFile */
        .highlight .c1 {{ color: #008000; font-style: italic; }} /* Comment.Single */
        .highlight .cs {{ color: #008000; font-style: italic; }} /* Comment.Special */
        .highlight .gd {{ color: #a31515; }} /* Generic.Deleted */
        .highlight .ge {{ font-style: italic; }} /* Generic.Emph */
        .highlight .gr {{ color: #ff0000; }} /* Generic.Error */
        .highlight .gh {{ color: #008080; font-weight: bold; }} /* Generic.Heading */
        .highlight .gi {{ color: #098658; }} /* Generic.Inserted */
        .highlight .go {{ color: #000000; }} /* Generic.Output */
        .highlight .gp {{ color: #008080; font-weight: bold; }} /* Generic.Prompt */
        .highlight .gs {{ font-weight: bold; }} /* Generic.Strong */
        .highlight .gu {{ color: #008080; font-weight: bold; }} /* Generic.Subheading */
        .highlight .gt {{ color: #ff0000; }} /* Generic.Traceback */
        .highlight .kc {{ color: #0000ff; font-weight: 500; }} /* Keyword.Constant - True, False, None */
        .highlight .kd {{ color: #0000ff; font-weight: 500; }} /* Keyword.Declaration */
        .highlight .kn {{ color: #af00db; font-weight: 500; }} /* Keyword.Namespace - import, from */
        .highlight .kp {{ color: #0000ff; font-weight: 500; }} /* Keyword.Pseudo */
        .highlight .kr {{ color: #0000ff; font-weight: 500; }} /* Keyword.Reserved */
        .highlight .kt {{ color: #267f99; font-weight: 500; }} /* Keyword.Type */
        .highlight .ld {{ color: #a31515; }} /* Literal.Date */
        .highlight .m {{ color: #098658; }} /* Literal.Number - 녹색 숫자 */
        .highlight .s {{ color: #a31515; }} /* Literal.String - 빨간색 문자열 */
        .highlight .na {{ color: #001080; }} /* Name.Attribute */
        .highlight .nb {{ color: #795e26; }} /* Name.Builtin - print, len, range 등 갈색 */
        .highlight .nc {{ color: #267f99; font-weight: 500; }} /* Name.Class - 청록색 강조 */
        .highlight .no {{ color: #0070c1; }} /* Name.Constant */
        .highlight .nd {{ color: #795e26; }} /* Name.Decorator - @decorator */
        .highlight .ni {{ color: #001080; }} /* Name.Entity */
        .highlight .ne {{ color: #267f99; }} /* Name.Exception */
        .highlight .nf {{ color: #795e26; font-weight: 400; }} /* Name.Function - 함수명 갈색 */
        .highlight .nl {{ color: #001080; }} /* Name.Label */
        .highlight .nn {{ color: #267f99; }} /* Name.Namespace */
        .highlight .nx {{ color: #001080; }} /* Name.Other */
        .highlight .py {{ color: #001080; }} /* Name.Property */
        .highlight .nt {{ color: #800000; }} /* Name.Tag */
        .highlight .nv {{ color: #001080; }} /* Name.Variable */
        .highlight .ow {{ color: #0000ff; }} /* Operator.Word */
        .highlight .w {{ color: #000000; }} /* Text.Whitespace */
        .highlight .mb {{ color: #098658; }} /* Literal.Number.Bin */
        .highlight .mf {{ color: #098658; }} /* Literal.Number.Float */
        .highlight .mh {{ color: #098658; }} /* Literal.Number.Hex */
        .highlight .mi {{ color: #098658; }} /* Literal.Number.Integer */
        .highlight .mo {{ color: #098658; }} /* Literal.Number.Oct */
        .highlight .sa {{ color: #a31515; }} /* Literal.String.Affix */
        .highlight .sb {{ color: #a31515; }} /* Literal.String.Backtick */
        .highlight .sc {{ color: #a31515; }} /* Literal.String.Char */
        .highlight .dl {{ color: #a31515; }} /* Literal.String.Delimiter */
        .highlight .sd {{ color: #008000; font-style: italic; }} /* Literal.String.Doc - Docstring */
        .highlight .s2 {{ color: #a31515; }} /* Literal.String.Double */
        .highlight .se {{ color: #ee0000; font-weight: 500; }} /* Literal.String.Escape - 이스케이프 강조 */
        .highlight .sh {{ color: #a31515; }} /* Literal.String.Heredoc */
        .highlight .si {{ color: #ee0000; font-weight: 500; }} /* Literal.String.Interpol - f-string 변수 */
        .highlight .sx {{ color: #a31515; }} /* Literal.String.Other */
        .highlight .sr {{ color: #811f3f; }} /* Literal.String.Regex */
        .highlight .s1 {{ color: #a31515; }} /* Literal.String.Single */
        .highlight .ss {{ color: #a31515; }} /* Literal.String.Symbol */
        .highlight .bp {{ color: #0070c1; font-style: italic; }} /* Name.Builtin.Pseudo - self, cls */
        .highlight .fm {{ color: #795e26; }} /* Name.Function.Magic - __init__, __str__ 등 */
        .highlight .vc {{ color: #001080; }} /* Name.Variable.Class */
        .highlight .vg {{ color: #001080; }} /* Name.Variable.Global */
        .highlight .vi {{ color: #001080; }} /* Name.Variable.Instance */
        .highlight .vm {{ color: #001080; }} /* Name.Variable.Magic */
        .highlight .il {{ color: #098658; }} /* Literal.Number.Integer.Long */

        /* Line numbers */
        .linenodiv {{
            background: #f5f5f5;
            padding: 20px 15px 20px 20px;
            border-right: 1px solid #e0e0e0;
        }}

        .linenodiv pre {{
            color: #999999;
            text-align: right;
            padding: 0;
            margin: 0;
            font-size: 13px;
        }}

        .linenos {{
            color: #999999;
            background: #f5f5f5;
            padding-right: 15px;
            margin-right: 15px;
            border-right: 1px solid #e0e0e0;
            user-select: none;
            font-size: 13px;
        }}

        /* 코드 테이블 구조 */
        .highlight table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .highlight td.linenos {{
            vertical-align: top;
            padding-left: 10px;
        }}

        .highlight td.code {{
            width: 100%;
            padding-left: 20px;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666666;
            margin-top: 50px;
            font-family: 'Segoe UI', sans-serif;
        }}

        .footer p {{
            margin: 5px 0;
        }}

        /* Scrollbar styling for light theme */
        ::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f5f5f5;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #c0c0c0;
            border-radius: 6px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #a0a0a0;
        }}
    </style>
    <script>
        // 코드 복사 기능
        function copyCode(button, fileIndex) {{
            const codeSection = document.querySelector(`#file-${{fileIndex}} .highlight`);
            const codeText = codeSection.innerText;

            navigator.clipboard.writeText(codeText).then(() => {{
                // 버튼 텍스트 변경
                const originalText = button.textContent;
                button.textContent = '✓ Copied!';
                button.classList.add('copied');

                // 2초 후 원래대로
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }}, 2000);
            }}).catch(err => {{
                console.error('복사 실패:', err);
                alert('코드 복사에 실패했습니다.');
            }});
        }}

        // 라인 번호 클릭 시 해당 라인으로 이동 (부드러운 스크롤)
        document.addEventListener('DOMContentLoaded', function() {{
            const lineNumbers = document.querySelectorAll('.linenos');
            lineNumbers.forEach(lineNum => {{
                lineNum.style.cursor = 'pointer';
            }});
        }});
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 NFS Report Module - Source Code</h1>
            <div class="meta">
                Generated on {date}<br>
                Total Files: {file_count} | Total Lines: {total_lines:,}
            </div>
        </div>

        <div class="toc">
            <h2>📑 Table of Contents</h2>
            <ul>
{toc_items}
            </ul>
        </div>

{file_sections}

        <div class="footer">
            <p>Generated by NFS Report Module Code Generator</p>
            <p>Syntax highlighting powered by Pygments</p>
            <p>© 2025 National Forensic Service</p>
        </div>
    </div>
</body>
</html>
"""

def generate_file_section_pygments(filepath, file_index):
    """Pygments를 사용한 파일 섹션 생성"""
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
        lines = code.split('\n')

    # Pygments로 syntax highlighting 적용
    formatter = HtmlFormatter(
        linenos='table',
        cssclass='highlight',
        style='monokai',  # VS Code Dark+와 유사한 스타일
        noclasses=False,
        linenospecial=0
    )

    lexer = PythonLexer()
    highlighted_code = highlight(code, lexer, formatter)

    section = f"""
    <div class="file-section" id="file-{file_index}">
        <div class="file-header">
            <h2>{filename}</h2>
            <div class="file-meta">
                {len(lines)} lines | {file_size:,} bytes
            </div>
            <button class="copy-button" onclick="copyCode(this, {file_index})">📋 Copy</button>
        </div>
        <div class="code-container">
            {highlighted_code}
        </div>
    </div>
"""
    return section, len(lines)

def escape_html(text):
    """HTML 특수 문자 이스케이프"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def generate_file_section_basic(filepath, file_index):
    """기본 syntax highlighting을 사용한 파일 섹션 생성 (Pygments 없을 때)"""
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 라인 번호 생성
    line_numbers = '\n'.join(f'<span class="linenos">{i}</span>'
                             for i in range(1, len(lines) + 1))

    # 코드 내용 (간단한 HTML 이스케이프만)
    code_lines = [escape_html(line.rstrip('\n')) for line in lines]
    code_content = '\n'.join(code_lines)

    section = f"""
    <div class="file-section" id="file-{file_index}">
        <div class="file-header">
            <h2>{filename}</h2>
            <div class="file-meta">
                {len(lines)} lines | {file_size:,} bytes
            </div>
            <button class="copy-button" onclick="copyCode(this, {file_index})">📋 Copy</button>
        </div>
        <div class="code-container">
            <pre><code><table class="highlight"><tr>
<td class="linenodiv"><pre>{line_numbers}</pre></td>
<td class="code"><pre>{code_content}</pre></td>
</tr></table></code></pre>
        </div>
    </div>
"""
    return section, len(lines)

def main():
    """메인 함수"""
    module_dir = Path(__file__).parent / 'module'

    # Python 파일 목록 (알파벳 순 정렬, __init__.py 제외)
    py_files = sorted([f for f in module_dir.glob('*.py')
                      if not f.name.startswith('__')])

    # TOC 아이템 생성
    toc_items = []
    file_sections = []
    total_lines = 0

    print("🔨 HTML 파일 생성 중...")
    print(f"{'=' * 60}")

    for idx, filepath in enumerate(py_files, 1):
        filename = filepath.name
        file_size = filepath.stat().st_size
        with open(filepath, 'r') as f:
            line_count = len(f.readlines())

        print(f"  [{idx:2d}/{len(py_files)}] {filename:<40} {line_count:4d} lines")

        toc_items.append(
            f'                <li><a href="#file-{idx}">'
            f'<span class="file-name">{filename}</span>'
            f'<span class="line-count">{line_count} lines</span>'
            f'</a></li>'
        )

        # Pygments 사용 여부에 따라 다른 함수 호출
        if PYGMENTS_AVAILABLE:
            section, lines = generate_file_section_pygments(filepath, idx)
        else:
            section, lines = generate_file_section_basic(filepath, idx)

        file_sections.append(section)
        total_lines += lines

    print(f"{'=' * 60}")

    # HTML 생성
    html = HTML_TEMPLATE.format(
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        file_count=len(py_files),
        total_lines=total_lines,
        toc_items='\n'.join(toc_items),
        file_sections='\n'.join(file_sections)
    )

    # 출력 파일 저장
    output_path = Path(__file__).parent / 'module_code.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HTML 파일 생성 완료!")
    print(f"📁 위치: {output_path}")
    print(f"📊 총 {len(py_files)}개 파일, {total_lines:,} 라인")
    print(f"🎨 테마: VS Code Light+ (인쇄 친화적)")
    print(f"🔧 Pygments: {'사용' if PYGMENTS_AVAILABLE else '미사용'}")

if __name__ == '__main__':
    main()
