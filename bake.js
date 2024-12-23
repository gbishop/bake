import { NumberedTextarea } from "./numbered-textarea.js";

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
  return Math.round(value * 10 ** digits) / 10 ** digits;
}

function fmt_grams(g = 0) {
  if (round(g, 0) >= 100) return g.toFixed(0) + "&numsp;&numsp;&numsp;";
  if (round(g, 1) >= 10) return g.toFixed(1) + "&numsp;";
  if (round(g, 2) >= 0.1) return g.toFixed(2);
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
 * @param {HTMLElement} container
 * @returns {InstanceType<T>}
 */
function queryElement(selector, type, container = document.body) {
  const el = container.querySelector(selector);
  if (!(el instanceof type)) {
    throw new Error(
      `Selector ${selector} matched ${el} which is not an ${type}`,
    );
  }
  return /** @type {InstanceType<T>} */ (el);
}

/** @param {HTMLDialogElement} dialog */
async function populateExamples(dialog) {
  const examplesData = await (await fetch("./examples.json")).json();
  const ul = queryElement("ul", HTMLUListElement, dialog);
  for (let key in examplesData) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = "#" + key;
    a.innerText = examplesData[key];
    li.appendChild(a);
    ul.appendChild(li);
  }
}

async function main() {
  const solve = await setupPython();
  const textarea = queryElement("numbered-textarea", NumberedTextarea);
  const solveButton = queryElement("button#solve", HTMLButtonElement);
  const showButton = queryElement("button#examples", HTMLButtonElement);
  const clearButton = queryElement("button#clear", HTMLButtonElement);
  const examplesButton = queryElement("dialog", HTMLDialogElement);
  const table = queryElement("table", HTMLTableElement);
  const message = queryElement("div#message", HTMLDivElement);
  populateExamples(examplesButton);

  document.body.classList.toggle("loading");
  solveButton.addEventListener("click", display);
  showButton.addEventListener("click", () => {
    examplesButton.showModal();
  });
  examplesButton.addEventListener("click", () => examplesButton.close());
  clearButton.addEventListener("click", () => {
    localStorage.setItem("recipe", "");
    textarea.value = "";
    table.innerHTML = "";
    location.hash = "";
  });
  textarea.addEventListener("input", () => {
    localStorage.setItem("recipe", textarea.value);
  });
  textarea.addEventListener("keydown", (event) => {
    if (event.key == "Enter" && event.shiftKey) {
      event.preventDefault();
      display();
    }
  });
  async function loadRecipe() {
    if (!location.hash.endsWith(".bake")) return;
    const resp = await fetch(`./recipes/${location.hash.slice(1)}`);
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
      if (!text) {
        table.innerHTML = "";
      }
    }
    localStorage.setItem("recipe", text);
    const proxy = solve(text);
    const result = proxy.toJs({ create_pyproxies: false });
    message.innerText = "";
    if (result.message) {
      message.innerText = result.message;
    }
    table.innerHTML = tabulate(headings, "tgt%ggg", result.rows || []);
  }
  display();
}

main();
