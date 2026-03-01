from pathlib import Path
import mammoth

src = Path("contract agreement/Template Agreement GT_ Supporting Legal System.docx")
html_out = Path("contract agreement/Template Agreement GT_ Supporting Legal System.mammoth.html")

with src.open("rb") as docx_file:
    result = mammoth.convert_to_html(docx_file)

html_out.write_text(result.value, encoding="utf-8")
print("Wrote:", html_out)
print("Warnings:", result.messages)
