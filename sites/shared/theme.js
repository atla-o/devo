(function () {
  var key = "devo-theme";

  function theme() {
    return document.documentElement.getAttribute("data-theme") === "rich" ? "rich" : "simple";
  }

  function apply(next) {
    document.documentElement.setAttribute("data-theme", next);
    var pressed = next === "rich" ? "true" : "false";
    document.querySelectorAll(".theme-switch").forEach(function (button) {
      button.setAttribute("aria-pressed", pressed);
    });
    try {
      localStorage.setItem(key, next);
    } catch (err) {}
  }

  if (new URLSearchParams(location.search).get("theme") === "rich") {
    document.documentElement.setAttribute("data-theme", "rich");
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".theme-switch");
    if (!button) return;
    apply(theme() === "rich" ? "simple" : "rich");
  });

  apply(theme());
})();
