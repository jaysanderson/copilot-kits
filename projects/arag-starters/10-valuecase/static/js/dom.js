// Minimal DOM builder shared by every view.
export function el(tag, attrs, children) {
  const node = document.createElement(tag);
  if (attrs) {
    Object.entries(attrs).forEach(([k, v]) => {
      if (v === null || v === undefined) return;
      if (k === "class") node.className = v;
      else if (k === "html") node.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v);
    });
  }
  (children || []).forEach((c) => {
    if (c === null || c === undefined) return;
    node.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
  });
  return node;
}

export function clear(node) {
  node.innerHTML = "";
}

export function escapeXml(s) {
  return String(s).replace(/[<>&'"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" }[c]));
}
