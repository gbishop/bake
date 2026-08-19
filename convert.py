# Convert .bake files to the new .html format

from tree import *
from pandas import DataFrame
import html
import re


def notesToHTML(text: str) -> str:
    # Escape standard HTML entities (<, >, &) to prevent rendering bugs
    text = html.escape(text.strip())

    text = re.sub(r"(\d+)([g%])", "\\1\u202f\\2", text)
    text = re.sub(r"(\d+)([FC])", "\\1°\\2", text)

    # Split text blocks divided by blank lines
    blocks = re.split(r"\n\s*\n", text)
    html_output = []

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        # Handle list blocks starting with '-'
        if any(line.startswith("- ") for line in lines):
            header_lines = []
            list_items = []

            for line in lines:
                if line.startswith("- "):
                    list_items.append(line[2:].strip())
                else:
                    header_lines.append(line)

            block_elements = []
            if header_lines:
                block_elements.append(
                    f"<p><strong>{' '.join(header_lines)}</strong></p>"
                )

            items_html = "\n".join(f"  <li>{item}</li>" for item in list_items)
            block_elements.append(f"<ul>\n{items_html}\n</ul>")
            html_output.append("\n".join(block_elements))

        else:
            # Rejoin line-wrapped paragraph text with spaces and keep '#' literal
            paragraph = " ".join(lines)
            html_output.append(f"<p>{paragraph}</p>")

    HTML = "\n\n".join(html_output)

    return HTML


def convert(filename: str, text: str, recipe: Recipe, solution: DataFrame):
    def value(part, name):
        g = solution.loc[(part, name), "value"]
        ga = abs(g)
        if round(ga, 0) >= 100:
            r = f"{g:.0f}"
        elif round(ga, 1) >= 5:
            r = f"{g:0.1f}"
        elif ga < 0.01:
            r = ""
        else:
            r = f"{g:0.2f}"
        return r

    comment = False
    notes = []
    rows = []
    part = ""
    for line in text.split("\n"):
        if line.startswith("/*+"):
            break

        elif line.startswith("/*"):
            comment = True

        elif line.startswith("*/"):
            comment = False

        elif comment:
            notes.append(line)

        elif line.startswith("#"):
            notes.append(line)

        elif m := re.match(r"(\w+)(\s*\^\s*)?(\d+[g%])?:.*", line):
            part, _, extra = m.groups()
            rows.append([part, "", "", value(part, "total")])
            if extra:
                rows.append(["", "extra", f"-{extra}", ""])

        elif m := re.match(r"\s+(\w+)(\s*=\s*([a-zA-Z_0-9.\+\-\*\/()% ]+))?", line):
            ingredient, _, formula = m.groups()
            v = value(part, ingredient) if ingredient != "hydration" else ""
            ingredient = re.sub(r"\btotal\b", "total_mass", ingredient)
            if formula:
                formula = re.sub(r"(\d+)ppm", "\\1e-6", formula)
                formula = re.sub(r"(\w+)\.total\b", "\\1", formula)
                formula = re.sub(r"\btotal\b", "total_mass", formula)
            rows.append(["", ingredient, formula or "", v])

    HTML = """
<html>
<head>
<style>
  #recipe-notes p, #recipe-notes ul, #recipe-notes ol { margin: 4px 0; }
  #recipe-notes h1 { margin: 0 0 4px 0; }
  #recipe-notes h2 { margin: 4px 0; }
  body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #222; }
  table { border-collapse: collapse; width: 100%; margin: 1.5rem 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background-color: #f5f5f5; }
  td:nth-child(4) { text-align: right; font: 16px "Courier New", Courier, monospace; }
  .recipe-notes { margin-top: 2rem; line-height: 1.2; }
</style>
</head>
<body>
  <table id="recipe-grid">
    <thead>
      <tr><th>part</th><th>name</th><th>formula</th><th>mass</th></tr>
    </thead>
    <tbody>
"""
    for row in rows:
        HTML += "<tr>"
        for column in row:
            HTML += f"<td>{column}</td>"
        HTML += "</tr>\n"

    HTML += f"""
    </tbody>
  </table>
  <div id="recipe-notes">
{notesToHTML("\n".join(notes))}
  </div>
</body>"""

    print(HTML.strip())
