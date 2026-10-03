(function () {
  var host = location.hostname;
  if (host === "devoutshaman.com" || host.endsWith(".devoutshaman.com")) return;
  document.querySelectorAll("a[data-local]").forEach(function (a) {
    a.setAttribute("href", a.getAttribute("data-local"));
  });
})();
