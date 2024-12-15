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

const example = `# Start with soft white bread and morph to whole grain

starter:
  rye
  water
  hydration = 60%

sponge ^ 2%: # allow for 2% loss
  starter = 10% * total_flour
  water
  oats = ww_flour
  ww_flour
  total_flour = 15%
  hydration = 100%

grain:
  prairie_gold
  hard_red
  spelt = 10%
  rye = 5%

wet:
  sponge
  water
  butter
  honey = 8%

dry:
  grain
  # half the water to milk
  nido = 50% * 13% * wet.water
  potato_flakes = 2%
  flaxseed_meal = 7%
  salt = 1.8% - 1.3% * wet.butter
  wgbi = 2%
  yeast = 0.4%
  sunflower_seeds = 10%

dough:
  wet
  dry
  total_water = 70%
  total_fat = 8%
  total_flour = 480g
`;

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
    console.log("display");
    let text = textarea.value;
    if (!text) {
      text = localStorage.getItem("recipe") || example;
      textarea.value = text;
    }
    localStorage.setItem("recipe", text);
    const proxy = solve(text);
    const result = proxy.toJs({ create_pyproxies: false });
    console.log("result", result);
    if (result.failed) {
      console.log("failed", result.message);
      console.log(message);
      message.innerText = result.message;
    }
    table.innerHTML = tabulate(headings, "tgt%ggg", result.rows || []);
  }
  display();
}
main();
