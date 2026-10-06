import React from "react";
import ReactDOM from "react-dom/client";
import App from "./QCWidget";
import "./qcWidget.css";

function mount(element: HTMLElement) {
  if (element.dataset.mounted) return;
  element.dataset.mounted = "true";
  ReactDOM.createRoot(element).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

function mountAll() {
  const targets = document.querySelectorAll<HTMLElement>(".qc-tree-app");
  if (targets.length) {
    targets.forEach(mount);
    return;
  }

  const standaloneRoot = document.getElementById("root");
  if (standaloneRoot) mount(standaloneRoot);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mountAll);
} else {
  mountAll();
}
