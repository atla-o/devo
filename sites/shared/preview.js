(function () {
  var host = location.hostname;
  if (host !== "localhost" && host !== "127.0.0.1" && host !== "::1") return;
  document.querySelectorAll("a[data-local]").forEach(function (a) {
    a.setAttribute("href", a.getAttribute("data-local"));
  });
})();
