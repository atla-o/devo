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

  var bar = document.querySelector(".topbar");
  var menuBtn = document.querySelector(".menu-toggle");
  var menuSheet = document.querySelector(".menu-sheet");

  function measureDrop() {
    var lines = document.querySelectorAll(".dropdown a.drop-line");
    if (!lines.length) return;
    var sample = window.getComputedStyle(lines[0]);
    var probe = document.createElement("span");
    probe.style.position = "absolute";
    probe.style.left = "-9999px";
    probe.style.top = "0";
    probe.style.visibility = "hidden";
    probe.style.whiteSpace = "nowrap";
    probe.style.font = sample.font;
    probe.style.letterSpacing = sample.letterSpacing;
    document.body.appendChild(probe);
    var max = 0;
    lines.forEach(function (el) {
      probe.textContent = (el.textContent || "").trim();
      var width = probe.getBoundingClientRect().width;
      if (width > max) max = width;
    });
    probe.remove();
    if (max > 0) {
      document.documentElement.style.setProperty("--drop-col", Math.ceil(max) + "px");
    }
  }

  function openCat(cat) {
    if (!bar || !cat) return;
    bar.setAttribute("data-open", cat);
  }

  function closeCat() {
    if (!bar) return;
    bar.removeAttribute("data-open");
  }

  document.querySelectorAll(".topitem[data-cat]").forEach(function (item) {
    var cat = item.getAttribute("data-cat");
    item.addEventListener("mouseenter", function () {
      openCat(cat);
    });
    item.addEventListener("focusin", function () {
      openCat(cat);
    });
  });
  if (bar) {
    bar.addEventListener("mouseleave", closeCat);
    bar.addEventListener("focusout", function (event) {
      if (!bar.contains(event.relatedTarget)) closeCat();
    });
  }

  measureDrop();
  window.addEventListener("resize", measureDrop);

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

  var asked = new URLSearchParams(location.search).get("theme");
  if (asked === "complex" || asked === "rich") {
    document.documentElement.setAttribute("data-theme", "complex");
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
