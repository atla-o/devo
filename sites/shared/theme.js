(function () {
  var key = "devo-theme";
  var branches = ["arcada", "mattercircle", "humanehealth", "lightround"];

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
    if (next === "rich") route();
  }

  function markActive(name) {
    document.querySelectorAll(".topnav a").forEach(function (link) {
      if (name && link.getAttribute("data-branch") === name) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function spy() {
    if (document.body.getAttribute("data-branch")) return;
    var line = window.innerHeight * 0.35;
    var name = branches[0];
    document.querySelectorAll(".panel").forEach(function (panel) {
      var box = panel.getBoundingClientRect();
      if (box.top <= line && box.bottom > line) name = panel.getAttribute("data-branch");
    });
    markActive(name);
  }

  function park(panel) {
    var barH = bar ? bar.offsetHeight : 0;
    var top = panel.getBoundingClientRect().top + window.scrollY - barH;
    window.scrollTo(0, Math.max(0, top));
  }

  function route() {
    var hash = (location.hash || "").replace("#", "");
    if (branches.indexOf(hash) !== -1) {
      document.body.setAttribute("data-branch", hash);
      window.scrollTo(0, 0);
      markActive(hash);
      return;
    }
    document.body.removeAttribute("data-branch");
    if (hash.indexOf("panel-") === 0) {
      var panel = document.getElementById(hash);
      markActive(hash.replace("panel-", ""));
      if (panel) {
        park(panel);
        requestAnimationFrame(function () {
          park(panel);
        });
      }
      return;
    }
    spy();
  }

  var bar = document.querySelector(".topbar");
  window.addEventListener(
    "scroll",
    function () {
      if (!bar) return;
      if (window.scrollY > 8) bar.classList.add("is-scrolled");
      else bar.classList.remove("is-scrolled");
      spy();
    },
    { passive: true }
  );

  if (new URLSearchParams(location.search).get("theme") === "rich") {
    document.documentElement.setAttribute("data-theme", "rich");
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".theme-switch");
    if (!button) return;
    apply(theme() === "rich" ? "simple" : "rich");
  });

  window.addEventListener("hashchange", route);
  apply(theme());
  route();
})();
