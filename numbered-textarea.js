/**
 * A text area with line numbers. I started with an idea from
 * https://dev.to/madsstoumann/line-numbers-for-using-svg-1216
 * and hacked it to generate the line number dynamically and
 * handle line wrapping.
 *
 * This CSS appears to be required:
 *
      textarea {
        background-attachment: local;
        background-position: 0 0;
        background-repeat: no-repeat;
        background-size: 5ch 100%;
        border: 1px solid #ccc;
        box-sizing: border-box;
        font-weight: normal;
        font-size: 0.85rem;
        line-height: 1.3;
        padding-block: 1.5ch;
        padding-inline: 7ch 2ch;
        transition: background-image 0.01s linear;
      }
 *
 */
class NumberedTextarea extends HTMLTextAreaElement {
  connectedCallback() {
    super.value = this.textContent || "";
    const bound = () => this.numberLines();
    const debounced = debounce(bound, 200);
    this.addEventListener("input", debounced);
    const resizeObserver = new ResizeObserver(debounced);
    resizeObserver.observe(this);
    this.addEventListener("input", debounced);
    debounced();
  }

  get value() {
    return super.value;
  }

  /** @param {string} v
   */
  set value(v) {
    super.value = v;
    this.numberLines();
  }

  backgroundURL = "";
  lastSVG = "";

  numberLines() {
    const style = getComputedStyle(this);
    const fontSize = parseFloat(style.fontSize);
    const lineHeight = parseFloat(style.lineHeight) / fontSize;
    const paddingTop = parseFloat(style.paddingTop) / 2;
    const translateY = (fontSize * lineHeight).toFixed(2);

    /* Collect the text commands for the line numbers */
    const numbers = [];
    const lines = super.value.split("\n");
    let N = 1;
    for (let i = 0; i < lines.length; i++) {
      // determine how many display lines this text line requires
      const mirror = document.createElement("div");
      copyNodeStyle(this, mirror);
      mirror.style.paddingTop = "0";
      mirror.style.paddingBottom = "0";
      mirror.style.height = `${translateY}px`;
      mirror.style.width = style.width;

      mirror.innerText = lines[i];
      document.body.appendChild(mirror);
      const step = Math.max(1, Math.round(mirror.scrollHeight / translateY));
      document.body.removeChild(mirror);
      const number = `<text x="80%" style="--n:${N};">${i + 1}</text>`;
      N += step;
      numbers.push(number);
    }
    /* build the svg */
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" style="background:${style.borderColor};">
      <style>
        text {
          fill: hsl(from ${style.color} h s l / 50%);
          font-family: ${style.fontFamily};
          font-size: ${style.fontSize};
          line-height: ${style.lineHeight};
          text-anchor: end;
          translate: 0 calc((var(--n) * ${translateY}px) + ${paddingTop}px);
        }
      </style>
      ${numbers.join("\n")}
    </svg>`;

    if (this.lastSVG != svg) {
      this.lastSVG = svg;

      /* convert it to a blog and get its URL */
      const blob = new Blob([svg], { type: "image/svg+xml" });
      if (this.backgroundURL) {
        URL.revokeObjectURL(this.backgroundURL);
      }
      this.backgroundURL = URL.createObjectURL(blob);
      this.style.backgroundImage = `url("${this.backgroundURL}")`;
    }
  }
}

customElements.define("numbered-textarea", NumberedTextarea, {
  extends: "textarea",
});

/** @param {function} callback
 * @param {number} wait
 */
function debounce(callback, wait) {
  let timeout;
  /** @param {any[]} args */
  return (...args) => {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => callback.apply(context, args), wait);
  };
}
function copyNodeStyle(sourceNode, targetNode) {
  const computedStyle = window.getComputedStyle(sourceNode);
  Array.from(computedStyle).forEach((key) =>
    targetNode.style.setProperty(
      key,
      computedStyle.getPropertyValue(key),
      computedStyle.getPropertyPriority(key),
    ),
  );
}
