(function () {
  document.querySelectorAll("[data-slides]").forEach(function (root) {
    var marks = root.querySelectorAll("[data-mark]");
    var buttons = root.querySelectorAll("[data-slide]");
    function show(index) {
      marks.forEach(function (mark, n) {
        if (n === index) mark.removeAttribute("hidden");
        else mark.setAttribute("hidden", "");
      });
      var frame = root.querySelector("svg");
      if (frame) frame.setAttribute("aria-label", "image " + (index + 1) + " of " + marks.length);
    }
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        show(Number(button.getAttribute("data-slide")));
      });
    });
    show(0);
  });

  var root = document.querySelector("[data-checkout]");
  if (!root) return;
  var house = root.getAttribute("data-house") || "";
  var key = "devo-store-cart";

  function read() {
    try {
      var parsed = JSON.parse(localStorage.getItem(key) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
      return [];
    }
  }

  function write(items) {
    localStorage.setItem(key, JSON.stringify(items));
  }

  var params = new URLSearchParams(location.search);
  var add = params.get("add");
  var n = params.get("n");
  var label = params.get("label");
  var items = read().filter(function (item) {
    return item.house === house;
  });
  if (add && n && label) {
    var id = house + ":" + add + ":" + n;
    var found = null;
    items.forEach(function (item) {
      if (item.id === id) found = item;
    });
    if (found) found.qty += 1;
    else items.push({ id: id, house: house, label: label, qty: 1 });
    write(
      read()
        .filter(function (item) {
          return item.house !== house;
        })
        .concat(items)
    );
    history.replaceState(null, "", location.pathname);
  }

  var list = root.querySelector("[data-items]");
  var offering = root.querySelector("[name=offering]");
  var pay = root.querySelector("[data-pay]");

  function persist() {
    write(
      read()
        .filter(function (item) {
          return item.house !== house;
        })
        .concat(items)
    );
  }

  function render() {
    if (!list) return;
    list.textContent = "";
    items.forEach(function (item) {
      var li = document.createElement("li");
      var name = document.createElement("span");
      name.textContent = item.label;
      var down = document.createElement("button");
      down.type = "button";
      down.setAttribute("data-qty", "-1");
      down.setAttribute("data-id", item.id);
      down.setAttribute("aria-label", "decrease " + item.label);
      down.textContent = "−";
      var qty = document.createElement("span");
      qty.textContent = String(item.qty);
      var up = document.createElement("button");
      up.type = "button";
      up.setAttribute("data-qty", "1");
      up.setAttribute("data-id", item.id);
      up.setAttribute("aria-label", "increase " + item.label);
      up.textContent = "+";
      li.appendChild(name);
      li.appendChild(down);
      li.appendChild(qty);
      li.appendChild(up);
      list.appendChild(li);
    });
    if (offering) {
      offering.value =
        items
          .map(function (item) {
            return item.label + " x" + item.qty;
          })
          .join(", ") || "checkout";
    }
    if (pay) pay.disabled = items.length === 0;
  }

  root.addEventListener("click", function (event) {
    var button = event.target.closest("[data-qty]");
    if (!button) return;
    var id = button.getAttribute("data-id");
    var delta = Number(button.getAttribute("data-qty"));
    items = items
      .map(function (item) {
        if (item.id !== id) return item;
        return { id: item.id, house: item.house, label: item.label, qty: item.qty + delta };
      })
      .filter(function (item) {
        return item.qty > 0;
      });
    persist();
    render();
  });

  render();
})();
