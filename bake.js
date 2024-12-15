async function setupPython() {
  // @ts-ignore
  let pyodide = await loadPyodide();
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");
  for (let i = 0; i < 3; i++) {
    try {
      await micropip.install("lark");
      break;
    } catch {
      console.log("waiting");
      await new Promise((resolve) => setInterval(resolve, 1000));
    }
  }
  await pyodide.loadPackage("numpy");
  // Downloading a single file
  await pyodide.runPythonAsync(`
from pyodide.http import pyfetch

for fname in ["solver.py", "ingredients.py"]:
  response = await pyfetch("./" + fname)
  with open(fname, "wb") as f:
    f.write(await response.bytes())
`);
  let pkg = pyodide.pyimport("solver");
  return pkg.solve;
}

function round(value = 0, digits = 0) {
  return Math.round(value * value ** digits) / value ** digits;
}

function fmt_grams(g = 0) {
  if (round(g, 0) >= 100) return g.toFixed(0) + "&numsp;&numsp;&numsp;";
  if (round(g, 1) >= 10) return g.toFixed(1) + "&numsp;";
  if (round(g, 2) >= 1) return g.toFixed(2);
  if (Math.abs(g) < 0.1) return "";
  return g.toString();
}

/** @param {number | string} value
 * @param {string} format
 */
function fmt_value(value, format) {
  if (typeof value == "string") return value;
  if (format == "%") return value.toFixed(1) + "%";
  if (format == "g") return fmt_grams(value);
  return value;
}

/**
 * @param {string[]} headings
 * @param {string} fmts
 * @param {(string | number)[][]} rows
 */
function tabulate(headings, fmts, rows) {
  const thead = `<thead>
    <tr>
      ${headings.map((heading) => `<th>${heading}</th>`).join("")}
    </tr>
  </thead>`;
  const tbody = `<tbody>
    ${rows
      .map(
        (row) => `
  <tr>
    ${row.map((col, i) => `<td>${fmt_value(col, fmts[i])}</td>`).join(" ")}
  </tr>`,
      )
      .join("\n")}
  </tbody>`;
  return `<table>
    ${thead}${tbody}
  </table>`;
}

const headings = ["Part", "Grams", "Ingredient", "%", "Flour", "Water", "Fat"];

/**
 * @template {typeof Element} T
 * @param {T} type
 * @param {string} selector
 * @returns {InstanceType<T>}
 */
function queryElement(selector, type) {
  const el = document.querySelector(selector);
  if (!(el instanceof type)) {
    throw new Error(
      `Selector ${selector} matched ${el} which is not an ${type}`,
    );
  }
  return /** @type {InstanceType<T>} */ (el);
}

async function main() {
  const solve = await setupPython();
  const textarea = queryElement("textarea", HTMLTextAreaElement);
  const button = queryElement("button#solve", HTMLButtonElement);
  const show = queryElement("button#examples", HTMLButtonElement);
  const examples = queryElement("dialog", HTMLDialogElement);
  const table = queryElement("table", HTMLTableElement);
  const message = queryElement("div#message", HTMLDivElement);
  document.body.classList.toggle("loading");
  button.addEventListener("click", display);
  show.addEventListener("click", () => {
    examples.showModal();
  });
  examples.addEventListener("click", () => examples.close());
  textarea.addEventListener("input", () => {
    localStorage.setItem("recipe", textarea.value);
  });
  textarea.addEventListener("keydown", (event) => {
    if (event.key == "Enter" && event.shiftKey) {
      event.preventDefault();
      display();
    }
  });
  lineNumbers(textarea, 100);
  async function loadRecipe() {
    const resp = await fetch(`./${location.hash.slice(1)}`);
    if (resp.ok) {
      let text = await resp.text();
      text = text.replace(/\/\*\+[\s\S]*\+\*\//m, "");
      textarea.value = text;
      display();
    } else {
      console.log("not found", location.hash);
    }
  }
  window.addEventListener("hashchange", loadRecipe);
  if (location.hash) {
    loadRecipe();
  }
  function display() {
    let text = textarea.value;
    if (!text) {
      text = localStorage.getItem("recipe") || "";
      textarea.value = text;
    }
    localStorage.setItem("recipe", text);
    const proxy = solve(text);
    const result = proxy.toJs({ create_pyproxies: false });
    message.innerText = "";
    if (result.failed) {
      console.log("failed", result.message);
      message.innerText = result.message;
    }
    table.innerHTML = tabulate(headings, "tgt%ggg", result.rows || []);
  }
  display();
}

/**
 * Add line numbers to a textarea from https://dev.to/madsstoumann/line-numbers-for-using-svg-1216
 * @param {HTMLElement} element
 * @param {number} numLines
 */
function lineNumbers(element, numLines) {
  const bgColor = getComputedStyle(element).borderColor;
  const fillColor = getComputedStyle(element).color;
  const fontFamily = getComputedStyle(element).fontFamily;
  const fontSize = parseFloat(getComputedStyle(element).fontSize);
  const lineHeight =
    parseFloat(getComputedStyle(element).lineHeight) / fontSize;
  const paddingTop = parseFloat(getComputedStyle(element).paddingTop) / 2;
  const translateY = (fontSize * lineHeight).toFixed(2);

  /* Note: In Safari, deduct `(paddingTop / 10)` from translateY */

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" style="background:${bgColor};">
    <style>
      text {
        fill: hsl(from ${fillColor} h s l / 50%);
        font-family: ${fontFamily};
        font-size: ${fontSize}px;
        line-height: ${lineHeight};
        text-anchor: end;
        translate: 0 calc((var(--n) * ${translateY}px) + ${paddingTop}px);
      }
    </style>
    ${Array.from({ length: numLines }, (_, i) => `<text x="80%" style="--n:${i + 1};">${i + 1}</text>`).join("")}
  </svg>`;

  element.style.backgroundImage = `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}

main();
