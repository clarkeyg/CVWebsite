/* ============================================================================
   GTC Development — site behaviour
   A small single-page site: six "screens" toggled client-side, driven by the
   URL hash so links are shareable and the browser back button works. No
   framework, no build step — to match the rest of this codebase.
   ============================================================================ */
(function () {
  "use strict";

  var SCREENS = ["home", "services", "work", "pricing", "about", "contact"];
  var screens = document.querySelectorAll("[data-screen]");
  var navLinks = document.querySelectorAll(".nav-link[data-nav]");
  var navMenu = document.getElementById("nav-links");
  var navToggle = document.querySelector(".nav-toggle");

  /* ---- Screen routing ---------------------------------------------------- */
  function showScreen(name, opts) {
    if (SCREENS.indexOf(name) === -1) name = "home";

    screens.forEach(function (el) {
      el.classList.toggle("is-active", el.getAttribute("data-screen") === name);
    });

    // Reflect the current screen on the nav (underline + aria-current).
    navLinks.forEach(function (link) {
      var active = link.getAttribute("data-nav") === name;
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });

    closeMenu();

    if (!opts || !opts.noScroll) {
      try { window.scrollTo({ top: 0, behavior: "auto" }); } catch (e) {}
      if (document.scrollingElement) document.scrollingElement.scrollTop = 0;
    }
  }

  function go(name) {
    // Updating the hash triggers the hashchange handler, which renders.
    if (("#" + name) === window.location.hash || (name === "home" && !window.location.hash)) {
      showScreen(name); // same hash — render directly (e.g. re-click Home)
    } else {
      window.location.hash = name;
    }
  }

  function currentScreen() {
    return (window.location.hash || "#home").replace(/^#\/?/, "") || "home";
  }

  window.addEventListener("hashchange", function () { showScreen(currentScreen()); });

  /* ---- Navigation clicks (nav, footer, in-page CTAs) --------------------- */
  document.addEventListener("click", function (e) {
    var trigger = e.target.closest("[data-nav]");
    if (!trigger) return;
    e.preventDefault();
    go(trigger.getAttribute("data-nav"));
  });

  /* ---- Mobile menu ------------------------------------------------------- */
  function closeMenu() {
    if (!navMenu) return;
    navMenu.classList.remove("is-open");
    if (navToggle) navToggle.setAttribute("aria-expanded", "false");
  }
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = navMenu.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (navMenu.classList.contains("is-open") && !e.target.closest(".nav")) closeMenu();
    });
    window.addEventListener("keydown", function (e) { if (e.key === "Escape") closeMenu(); });
  }

  /* ---- Work filters ------------------------------------------------------ */
  var filters = document.querySelectorAll(".filter[data-filter]");
  var workCards = document.querySelectorAll(".work-card[data-kind]");
  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var kind = btn.getAttribute("data-filter");
      filters.forEach(function (f) { f.classList.toggle("is-active", f === btn); });
      workCards.forEach(function (card) {
        var show = kind === "all" || card.getAttribute("data-kind") === kind;
        card.style.display = show ? "" : "none";
      });
    });
  });

  /* ---- Contact form ------------------------------------------------------ */
  var form = document.getElementById("contact-form");
  if (form) {
    var errorEl = document.getElementById("cf-error");
    var submitBtn = document.getElementById("cf-submit");
    var successEl = document.getElementById("contact-success");

    function showError(msg) {
      if (!errorEl) return;
      errorEl.textContent = msg;
      errorEl.hidden = false;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (errorEl) errorEl.hidden = true;

      if (!form.reportValidity()) return;

      var data = new FormData(form);
      submitBtn.disabled = true;
      var originalLabel = submitBtn.textContent;
      submitBtn.textContent = "Sending…";

      fetch("contact", {
        method: "POST",
        headers: { Accept: "application/json" },
        body: data,
      })
        .then(function (res) {
          return res.json().catch(function () { return {}; }).then(function (body) {
            return { ok: res.ok, body: body };
          });
        })
        .then(function (result) {
          if (result.ok && result.body && result.body.ok) {
            form.hidden = true;
            if (successEl) successEl.hidden = false;
            try { window.scrollTo({ top: 0 }); } catch (err) {}
          } else {
            var msg = (result.body && result.body.error) ||
              "Something went wrong sending your message. Please email me directly at clarkegeorge0509@gmail.com.";
            showError(msg);
            submitBtn.disabled = false;
            submitBtn.textContent = originalLabel;
          }
        })
        .catch(function () {
          showError("Couldn't reach the server. Please email me directly at clarkegeorge0509@gmail.com.");
          submitBtn.disabled = false;
          submitBtn.textContent = originalLabel;
        });
    });
  }

  /* ---- Initial render ---------------------------------------------------- */
  showScreen(currentScreen(), { noScroll: true });
})();
