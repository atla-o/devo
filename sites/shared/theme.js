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

  var bar = document.querySelector(".topbar");
  var menuBtn = document.querySelector(".menu-toggle");
  var menuSheet = document.querySelector(".menu-sheet");

  function setMenu(open) {
    if (!menuBtn || !menuSheet) return;
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    menuSheet.classList.toggle("is-open", open);
    document.body.classList.toggle("menu-open", open);
  }

  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      setMenu(menuBtn.getAttribute("aria-expanded") !== "true");
    });
  }
  if (menuSheet) {
    menuSheet.addEventListener("click", function (event) {
      if (event.target.closest("a")) setMenu(false);
    });
  }
  window.addEventListener(
    "scroll",
    function () {
      if (!bar) return;
      if (window.scrollY > 8) bar.classList.add("is-scrolled");
      else bar.classList.remove("is-scrolled");
    },
    { passive: true }
  );

  if (new URLSearchParams(location.search).get("theme") === "rich") {
    document.documentElement.setAttribute("data-theme", "rich");
  }

  var flipping = false;

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".theme-switch");
    if (!button || flipping) return;
    var next = theme() === "rich" ? "simple" : "rich";
    flipping = true;
    var cls = next === "rich" ? "is-flipping-down" : "is-flipping-up";
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
