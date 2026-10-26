(() => {
  const buttons = Array.from(document.querySelectorAll(".tab-button"));
  const panels = Array.from(document.querySelectorAll(".tab-panel"));

  function activate(tabName) {
    buttons.forEach((button) => {
      const selected = button.dataset.tab === tabName;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-selected", selected ? "true" : "false");
    });
    panels.forEach((panel) => {
      const selected = panel.id === `tab-${tabName}`;
      panel.classList.toggle("is-active", selected);
      panel.hidden = !selected;
    });
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      activate(button.dataset.tab);
    });
  });
})();
