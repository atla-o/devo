(function () {
  var API = "/api/aca/applications";
  var RECEIPT_KEY = "devo_aca_receipt";
  var EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  var ZIP_RE = /^\d{5}(?:-?\d{4})?$/;
  var RECEIPT_RE = /^aca_[0-9a-f]{16}$/;

  var form = document.getElementById("aca-form");
  var lookupForm = document.getElementById("lookup-form");
  var formError = document.getElementById("form-error");
  var submitBtn = document.getElementById("submit-btn");
  var statusCard = document.getElementById("status-card");
  var statusLabel = document.getElementById("status-label");
  var statusDetail = document.getElementById("status-detail");
  var statusMeta = document.getElementById("status-meta");

  function clearErrors(root) {
    root.querySelectorAll(".field-error").forEach(function (el) {
      el.textContent = "";
    });
    if (formError) formError.textContent = "";
  }

  function showErrors(root, fields) {
    Object.keys(fields || {}).forEach(function (key) {
      var el = root.querySelector('[data-error-for="' + key + '"]');
      if (el) el.textContent = fields[key];
    });
    if (fields && fields._form && formError) formError.textContent = fields._form;
  }

  function digits(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function clientErrors(data) {
    var fields = {};
    if (!data.name || data.name.trim().length < 2) fields.name = "Enter your name.";
    if (!EMAIL_RE.test(data.email || "")) fields.email = "Enter a valid email.";
    var phone = digits(data.phone);
    if (phone.length === 11 && phone.charAt(0) === "1") phone = phone.slice(1);
    if (phone.length !== 10) fields.phone = "Enter a 10-digit US phone number.";
    if (!data.state) fields.state = "Choose a state.";
    if (!ZIP_RE.test(String(data.zip || "").trim())) {
      fields.zip = "Enter a 5-digit ZIP code.";
    }
    var household = Number(data.household_size);
    if (!Number.isInteger(household) || household < 1 || household > 15) {
      fields.household_size = "Household size must be 1–15.";
    }
    if (!data.income_band) fields.income_band = "Choose an income range.";
    if (data.preferred_contact !== "email" && data.preferred_contact !== "phone") {
      fields.preferred_contact = "Choose email or phone.";
    }
    return fields;
  }

  function payloadFromForm() {
    var data = new FormData(form);
    return {
      name: String(data.get("name") || "").trim(),
      email: String(data.get("email") || "").trim(),
      phone: String(data.get("phone") || "").trim(),
      state: String(data.get("state") || "").trim(),
      zip: String(data.get("zip") || "").trim(),
      household_size: Number(data.get("household_size")),
      income_band: String(data.get("income_band") || "").trim(),
      preferred_contact: String(data.get("preferred_contact") || "").trim(),
      notes: String(data.get("notes") || "").trim(),
    };
  }

  function renderStatus(app) {
    if (!app || !statusCard) return;
    statusLabel.textContent = app.status_label || "Received";
    statusDetail.textContent = app.status_detail || "";
    var bits = [];
    if (app.receipt_id) bits.push("Receipt " + app.receipt_id);
    if (app.created_at) bits.push("Submitted " + app.created_at.replace("T", " ").replace("Z", " UTC"));
    if (app.email) bits.push(app.email);
    statusMeta.textContent = bits.join(" · ");
    statusCard.hidden = false;
  }

  function remember(app) {
    try {
      if (app && app.receipt_id) localStorage.setItem(RECEIPT_KEY, app.receipt_id);
    } catch (err) {
      /* private mode */
    }
  }

  function rememberedReceipt() {
    try {
      return localStorage.getItem(RECEIPT_KEY) || "";
    } catch (err) {
      return "";
    }
  }

  function lookupUrl(receipt, email) {
    if (receipt) return API + "?receipt_id=" + encodeURIComponent(receipt);
    return API + "?email=" + encodeURIComponent(email);
  }

  function fetchStatus(receipt, email) {
    return fetch(lookupUrl(receipt, email), {
      headers: { Accept: "application/json" },
    }).then(function (res) {
      return res.json().then(function (body) {
        return { ok: res.ok, status: res.status, body: body };
      });
    });
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      clearErrors(form);
      var payload = payloadFromForm();
      var errors = clientErrors(payload);
      if (Object.keys(errors).length) {
        showErrors(form, errors);
        return;
      }
      submitBtn.disabled = true;
      fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (res) {
          return res.json().then(function (body) {
            return { ok: res.ok, body: body };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            if (result.body && result.body.fields) showErrors(form, result.body.fields);
            if (formError) {
              formError.textContent =
                (result.body && result.body.error && result.body.error !== "validation"
                  ? result.body.error
                  : "") || "Could not submit. Check the form and try again.";
            }
            return;
          }
          remember(result.body);
          renderStatus(result.body);
          form.reset();
          statusCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        })
        .catch(function () {
          if (formError) formError.textContent = "Could not submit. Try again.";
        })
        .then(function () {
          submitBtn.disabled = false;
        });
    });
  }

  if (lookupForm) {
    lookupForm.addEventListener("submit", function (event) {
      event.preventDefault();
      clearErrors(lookupForm);
      var value = String(document.getElementById("lookup").value || "").trim();
      if (!value) {
        showErrors(lookupForm, { lookup: "Enter a receipt ID or email." });
        return;
      }
      var receipt = RECEIPT_RE.test(value) ? value : "";
      var email = EMAIL_RE.test(value) ? value : "";
      if (!receipt && !email) {
        showErrors(lookupForm, { lookup: "Use a receipt ID (aca_…) or email." });
        return;
      }
      fetchStatus(receipt, email)
        .then(function (result) {
          if (!result.ok) {
            showErrors(lookupForm, {
              lookup: (result.body && result.body.error) || "Application not found.",
            });
            return;
          }
          remember(result.body);
          renderStatus(result.body);
          statusCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        })
        .catch(function () {
          showErrors(lookupForm, { lookup: "Could not look up status." });
        });
    });
  }

  var saved = rememberedReceipt();
  if (saved && RECEIPT_RE.test(saved)) {
    fetchStatus(saved, "").then(function (result) {
      if (result.ok) renderStatus(result.body);
    }).catch(function () {});
  }
})();
