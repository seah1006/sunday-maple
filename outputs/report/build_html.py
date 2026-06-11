import base64
import re
from pathlib import Path

import markdown

REPORT_DIR = Path(__file__).resolve().parent
MD_PATH = REPORT_DIR / "final_report.md"
HTML_PATH = REPORT_DIR / "final_report.html"

text = MD_PATH.read_text(encoding="utf-8")
body = markdown.markdown(text, extensions=["extra", "sane_lists"])


def embed(match: re.Match) -> str:
    src = match.group(1)
    img_path = (REPORT_DIR / src).resolve()
    data = base64.b64encode(img_path.read_bytes()).decode("ascii")
    return f'src="data:image/png;base64,{data}"'


body = re.sub(r'src="([^"]+\.png)"', embed, body)

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Malgun Gothic", "맑은 고딕", system-ui, sans-serif;
  max-width: 820px; margin: 0 auto; padding: 32px 24px;
  color: #1a1a1a; line-height: 1.75; font-size: 15px;
  word-break: keep-all; overflow-wrap: anywhere;
}
h1 {
  font-size: 26px; text-align: center; line-height: 1.4;
  margin: 0 0 28px; padding-bottom: 18px; border-bottom: 3px solid #2c3e50;
}
h2 {
  font-size: 20px; margin: 34px 0 12px; padding: 6px 0 6px 12px;
  border-left: 5px solid #2c3e50; background: #f4f6f8;
  break-after: avoid; page-break-after: avoid;
}
h3 {
  font-size: 16px; margin: 22px 0 8px; color: #2c3e50;
  break-after: avoid; page-break-after: avoid;
}
p { margin: 10px 0; orphans: 3; widows: 3; }
img {
  display: block; max-width: 100%; height: auto; margin: 14px auto 20px;
  border: 1px solid #e2e6ea;
  break-inside: avoid; page-break-inside: avoid;
}
code {
  font-family: Consolas, "D2Coding", monospace; font-size: 0.92em;
  background: #eef1f3; padding: 1px 5px; border-radius: 3px;
}
@media print {
  body { max-width: none; padding: 0; font-size: 11.5pt; }
  h1 { font-size: 20pt; }
  h2 { font-size: 15pt; background: #f4f6f8 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  a { color: inherit; text-decoration: none; }
}
"""

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>선데이메이플 정규 보상 패턴 분석 최종 리포트</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""

HTML_PATH.write_text(html, encoding="utf-8")
print("작성:", HTML_PATH)
print("크기:", round(HTML_PATH.stat().st_size / 1024, 1), "KB")
print("내장 이미지 수:", html.count("data:image/png;base64,"))
print("남은 외부 png 링크:", len(re.findall(r'src="(?!data:)[^"]+\.png"', html)))
