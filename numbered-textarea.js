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
        padding-inline-start: 7ch;
        padding-inline-end: calc(100% - 7ch - round(down, 100% - 7ch, 1ch));
        transition: background-image 0.01s linear;
      }
 *
 */
export class NumberedTextarea extends HTMLTextAreaElement {
  static observedAttributes = ["nodebounce"];

  constructor() {
    super();
    this.lineCount = 0;
    this.numberLines = debounce(this._numberLines.bind(this), 100);
  }

  /**
   * @param {string} name
   * @param {string} oldValue
   * @param {string} newValue
   */
  attributeChangedCallback(name, oldValue, newValue) {
    console.log("attribute changed", name, oldValue, newValue);
    const bound = this._numberLines.bind(this);
    if (newValue == "true") {
      console.log("nodebounce");
      this.numberLines = bound;
    } else {
      this.numberLines = debounce(bound, 100);
    }
  }

  connectedCallback() {
    super.value = this.textContent || "";
    this.addEventListener("input", this.numberLines);
    const resizeObserver = new ResizeObserver(this.numberLines);
    resizeObserver.observe(this);
    this.addEventListener("input", this.numberLines);
    this.numberLines();
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

  _numberLines() {
    const style = getComputedStyle(this);
    const lineHeight = parseFloat(style.lineHeight);
    const paddingTop = parseFloat(style.paddingTop) / 2;

    /* Collect the text commands for the line numbers */
    const numbers = [];
    const lines = super.value.split("\n");

    // create a mirror node with the same style as the textarea
    const mirror = document.createElement("div");
    copyStyle(this, mirror);
    mirror.style.paddingTop = "0";
    mirror.style.paddingBottom = "0";
    mirror.style.height = `${lineHeight}px`;
    document.body.appendChild(mirror);

    this.lineCount = 0;
    for (let i = 0; i < lines.length; i++) {
      // determine how many display lines this text line requires
      mirror.innerText = lines[i];
      const increment = Math.max(
        1,
        Math.round(mirror.scrollHeight / lineHeight),
      );
      const number = `<text x="80%" style="--n:${this.lineCount + 1};">${i + 1}</text>`;
      this.lineCount += increment;
      numbers.push(number);
    }
    document.body.removeChild(mirror);
    /* build the svg */
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" style="background:${style.borderColor};">
      <style>
        text {
          fill: hsl(from ${style.color} h s l / 50%);
          font-family: ${style.fontFamily};
          font-size: ${style.fontSize};
          line-height: ${style.lineHeight};
          text-anchor: end;
          translate: 0 calc((var(--n) * ${lineHeight.toFixed(2)}px) + ${paddingTop}px);
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
      this.style.backgroundAttachment = "local";
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
  return () => {
    clearTimeout(timeout);
    timeout = setTimeout(callback, wait);
  };
}
/** @param {HTMLElement} sourceNode
 * @param {HTMLElement} targetNode
 */
function copyStyle(sourceNode, targetNode) {
  const computedStyle = getComputedStyle(sourceNode);
  Array.from(computedStyle).forEach((key) =>
    targetNode.style.setProperty(
      key,
      computedStyle.getPropertyValue(key),
      computedStyle.getPropertyPriority(key),
    ),
  );
}
