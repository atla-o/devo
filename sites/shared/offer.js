(function () {
  var key = "devo-theme";

  function theme() {
    var value = document.documentElement.getAttribute("data-theme");
    return value === "complex" || value === "rich" ? "complex" : "simple";
  }

  function apply(next) {
    document.documentElement.setAttribute("data-theme", next);
    var pressed = next === "complex" ? "true" : "false";
    document.querySelectorAll(".theme-switch").forEach(function (button) {
      button.setAttribute("aria-pressed", pressed);
    });
    try {
      localStorage.setItem(key, next);
    } catch (err) {}
  }

  var flipping = false;
  document.addEventListener("click", function (event) {
    var button = event.target.closest(".theme-switch");
    if (!button || flipping) return;
    var next = theme() === "complex" ? "simple" : "complex";
    flipping = true;
    var cls = next === "complex" ? "is-flipping-down" : "is-flipping-up";
    button.classList.remove("is-flipping-down", "is-flipping-up");
    void button.offsetWidth;
    button.classList.add(cls);
    var done = false;
    function finish() {
      if (done) return;
      done = true;
      apply(next);
      button.classList.remove(cls);
      flipping = false;
    }
    button.addEventListener("animationend", finish, { once: true });
    setTimeout(finish, 750);
  });

  apply(theme());
})();
