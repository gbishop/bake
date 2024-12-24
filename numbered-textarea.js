/**
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
export class NumberedTextarea extends HTMLElement {
  static observedAttributes = ["nodebounce", "placeholder"];

  constructor() {
    super();
    this.lineCount = 0;
    this.numberLines = debounce(this._numberLines.bind(this), 100);
    this.text = document.createElement("textarea");
    this.numbers = document.createElement("textarea");
    this.mirror = document.createElement("textarea");
  }

  /**
   * @param {string} name
   * @param {string} oldValue
   * @param {string} newValue
   */
  attributeChangedCallback(name, oldValue, newValue) {
    if (name == "nodebounce") {
      const bound = this._numberLines.bind(this);
      if (newValue == "true") {
        this.numberLines = bound;
      } else {
        this.numberLines = debounce(bound, 100);
      }
    } else if (name == "placeholder") {
      this.text.placeholder = newValue;
    }
  }

  connectedCallback() {
    const box = document.createElement("div");
    this.appendChild(box);
    this.numbers.className = "numbers";
    box.appendChild(this.numbers);
    box.appendChild(this.text);
    this.text.className = "text";
    this.appendChild(this.mirror);
    this.mirror.className = "mirror";
    this.text.addEventListener("input", this.numberLines);
    const resizeObserver = new ResizeObserver(this.numberLines);
    resizeObserver.observe(this);
    this.numberLines();
    // lock scrolling of text and numbers together
    let scrolling = null;
    const scrollTogether = (/** @type {Event} */ event) => {
      if (event.target != scrolling) {
        if (event.target == this.text) {
          scrolling = this.numbers;
          this.numbers.scrollTo({
            top: this.text.scrollTop,
            behavior: "instant",
          });
        } else {
          scrolling = this.text;
          this.text.scrollTo({
            top: this.numbers.scrollTop,
            behavior: "instant",
          });
        }
      } else {
        scrolling = null;
      }
    };
    this.text.addEventListener("scroll", scrollTogether);
    this.numbers.addEventListener("scroll", scrollTogether);
  }

  get value() {
    return this.text.value;
  }

  /** @param {string} v
   */
  set value(v) {
    // @ts-ignore
    this.text.value = v;
    this.numberLines();
  }

  get scrollHeight() {
    return this.text.scrollHeight;
  }

  _numberLines() {
    const numbers = [];
    const lines = this.text.value.split("\n");

    copyStyle(this.text, this.mirror);
    this.mirror.style.paddingTop = "0";
    this.mirror.style.paddingBottom = "0";
    this.mirror.style.height = "1lh";
    this.mirror.style.visibility = "hidden";
    this.mirror.style.position = "absolute";
    this.mirror.style.top = "0";
    this.mirror.style.left = "0";
    const lineHeight = this.mirror.getBoundingClientRect().height;

    this.lineCount = 0;
    for (let i = 0; i < lines.length; i++) {
      // determine how many display lines this text line requires
      let skip = 0;
      if (lines[i]) {
        this.mirror.innerText = lines[i];
        skip = Math.max(
          0,
          Math.round(this.mirror.scrollHeight / lineHeight) - 1,
        );
      }
      numbers.push(i + 1);
      for (let j = 0; j < skip; j++) numbers.push("");
      this.lineCount += 1 + skip;
    }
    this.numbers.value = numbers.join("\n");
  }
}

customElements.define("numbered-textarea", NumberedTextarea);

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
  const sourceStyle = getComputedStyle(sourceNode);
  const targetStyle = getComputedStyle(targetNode);
  Array.from(sourceStyle).forEach((key) => {
    if (
      targetStyle.getPropertyValue(key) != sourceStyle.getPropertyValue(key) ||
      targetStyle.getPropertyPriority(key) !=
        sourceStyle.getPropertyPriority(key)
    ) {
      targetNode.style.setProperty(
        key,
        sourceStyle.getPropertyValue(key),
        sourceStyle.getPropertyPriority(key),
      );
    }
  });
}
