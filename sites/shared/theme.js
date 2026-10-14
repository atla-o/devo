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
    document.querySelectorAll(".topitem > a").forEach(function (link) {
      if (name && link.getAttribute("data-branch") === name) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function spy() {
    if (document.body.getAttribute("data-branch")) return;
    var line = window.innerHeight * 0.42;
    var hits = [];
    document.querySelectorAll(".panel").forEach(function (panel) {
      var box = panel.getBoundingClientRect();
      if (box.top <= line && box.bottom > line) hits.push(panel);
    });
    markActive(hits.length === 1 ? hits[0].getAttribute("data-branch") : "");
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
      spy();
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

  window.addEventListener("hashchange", route);
  apply(theme());
  route();
})();
