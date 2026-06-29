/* ============================================================================
   Maple Street — Coffee & Kitchen (DEMO)
   Drives the interactive bits of the example café site: a menu rendered from
   data (the "menu that updates itself"), category tabs, and an order basket
   with live totals. No framework, no build step — to match the GTC codebase.
   Nothing here talks to a server: placing an order just shows a confirmation.
   ============================================================================ */
(function () {
  "use strict";

  /* ---- Menu data --------------------------------------------------------- */
  /* One source of truth: change a price or add a dish here and the page (and a
     café owner's real menu, in a production build) updates everywhere. */
  var MENU = {
    coffee: [
      { id: "flatwhite", emoji: "☕", name: "Flat white", desc: "Double ristretto, silky steamed milk.", price: 3.4 },
      { id: "latte", emoji: "🥛", name: "Caffè latte", desc: "Smooth house espresso, lots of milk.", price: 3.6 },
      { id: "capp", emoji: "☕", name: "Cappuccino", desc: "Espresso, steamed milk, velvet foam.", price: 3.5 },
      { id: "filter", emoji: "🫗", name: "Batch filter", desc: "Today's single-origin, brewed fresh.", price: 2.9, tag: "SINGLE ORIGIN" },
      { id: "mocha", emoji: "🍫", name: "Mocha", desc: "Espresso, 70% dark chocolate, milk.", price: 3.9 },
      { id: "espresso", emoji: "⚡", name: "Espresso", desc: "A short, bright shot of house blend.", price: 2.5 },
    ],
    brunch: [
      { id: "avo", emoji: "🥑", name: "Avocado & chilli toast", desc: "Sourdough, smashed avo, chilli, lime.", price: 8.5, tag: "VEGAN" },
      { id: "eggs", emoji: "🍳", name: "Eggs Benedict", desc: "Poached eggs, ham, hollandaise, muffin.", price: 9.5 },
      { id: "pancakes", emoji: "🥞", name: "Buttermilk pancakes", desc: "Maple syrup, seasonal berries, cream.", price: 8.0 },
      { id: "shak", emoji: "🍅", name: "Shakshuka", desc: "Baked eggs, spiced tomato, feta, bread.", price: 9.0 },
      { id: "granola", emoji: "🥣", name: "House granola", desc: "Toasted oats, yoghurt, honey, fruit.", price: 6.5, tag: "VEG" },
      { id: "toastie", emoji: "🧀", name: "Three-cheese toastie", desc: "Melted cheddar, gruyère, mozzarella.", price: 7.0 },
    ],
    bakery: [
      { id: "croissant", emoji: "🥐", name: "Butter croissant", desc: "Laminated by hand, baked at dawn.", price: 3.2 },
      { id: "almond", emoji: "🥐", name: "Almond croissant", desc: "Frangipane filled, sugar dusted.", price: 3.8, tag: "FAVOURITE" },
      { id: "cinnamon", emoji: "🌀", name: "Cinnamon swirl", desc: "Soft, gooey, cream-cheese glaze.", price: 3.6 },
      { id: "banana", emoji: "🍌", name: "Banana bread", desc: "Toasted, with salted butter.", price: 3.4 },
      { id: "brownie", emoji: "🍫", name: "Sea-salt brownie", desc: "Fudgy centre, flaky salt top.", price: 3.0 },
      { id: "cookie", emoji: "🍪", name: "Brown-butter cookie", desc: "Crisp edges, chewy middle.", price: 2.6 },
    ],
    cold: [
      { id: "icedlatte", emoji: "🧊", name: "Iced latte", desc: "Espresso over ice and cold milk.", price: 3.8 },
      { id: "coldbrew", emoji: "🥤", name: "Cold brew", desc: "Steeped 18 hours, smooth & strong.", price: 3.9, tag: "SLOW STEEP" },
      { id: "matcha", emoji: "🍵", name: "Iced matcha", desc: "Ceremonial matcha, oat milk.", price: 4.2, tag: "VEGAN" },
      { id: "lemonade", emoji: "🍋", name: "Cloudy lemonade", desc: "Pressed lemons, lightly sweet.", price: 3.2 },
      { id: "smoothie", emoji: "🍓", name: "Berry smoothie", desc: "Mixed berries, banana, yoghurt.", price: 4.5 },
      { id: "sparkling", emoji: "💧", name: "Sparkling water", desc: "Local, lightly carbonated.", price: 2.2 },
    ],
  };

  // Flat lookup so the basket can resolve any item by id regardless of category.
  var ITEMS = {};
  Object.keys(MENU).forEach(function (cat) {
    MENU[cat].forEach(function (item) { ITEMS[item.id] = item; });
  });

  var fmt = function (n) { return "£" + n.toFixed(2); };

  /* ---- Render the menu --------------------------------------------------- */
  var grid = document.getElementById("menu-grid");

  function renderCategory(cat) {
    if (!grid) return;
    grid.innerHTML = "";
    MENU[cat].forEach(function (item) {
      var el = document.createElement("article");
      el.className = "dish";
      var tag = item.tag ? '<span class="dish-tag">' + item.tag + "</span>" : "";
      el.innerHTML =
        '<div class="dish-emoji" aria-hidden="true">' + item.emoji + "</div>" +
        '<div class="dish-main"><h3>' + item.name + tag + "</h3><p>" + item.desc + "</p></div>" +
        '<div class="dish-side"><span class="dish-price">' + fmt(item.price) + "</span>" +
        '<button class="dish-add" data-add="' + item.id + '">Add</button></div>';
      grid.appendChild(el);
    });
    syncAddButtons();
  }

  /* ---- Menu tabs --------------------------------------------------------- */
  var tabs = document.querySelectorAll(".menu-tab[data-cat]");
  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", on ? "true" : "false");
      });
      renderCategory(tab.getAttribute("data-cat"));
    });
  });

  /* ---- Basket ------------------------------------------------------------ */
  var basket = {}; // id -> qty
  var itemsEl = document.getElementById("basket-items");
  var emptyEl = document.getElementById("basket-empty");
  var countEl = document.getElementById("basket-count");
  var totalEl = document.getElementById("basket-total");
  var checkoutBtn = document.getElementById("basket-checkout");

  function basketCount() {
    return Object.keys(basket).reduce(function (n, id) { return n + basket[id]; }, 0);
  }
  function basketTotal() {
    return Object.keys(basket).reduce(function (sum, id) {
      return sum + ITEMS[id].price * basket[id];
    }, 0);
  }

  function add(id) {
    basket[id] = (basket[id] || 0) + 1;
    renderBasket();
  }
  function change(id, delta) {
    basket[id] = (basket[id] || 0) + delta;
    if (basket[id] <= 0) delete basket[id];
    renderBasket();
  }

  function renderBasket() {
    var ids = Object.keys(basket);
    if (itemsEl) itemsEl.innerHTML = "";

    ids.forEach(function (id) {
      var item = ITEMS[id];
      var li = document.createElement("li");
      li.className = "basket-item";
      li.innerHTML =
        '<span class="basket-item-name">' + item.name + "</span>" +
        '<span class="qty">' +
          '<button data-dec="' + id + '" aria-label="Remove one ' + item.name + '">−</button>' +
          '<span class="qty-val">' + basket[id] + "</span>" +
          '<button data-inc="' + id + '" aria-label="Add one ' + item.name + '">+</button>' +
        "</span>" +
        '<span class="basket-item-price">' + fmt(item.price * basket[id]) + "</span>";
      if (itemsEl) itemsEl.appendChild(li);
    });

    var count = basketCount();
    if (emptyEl) emptyEl.hidden = ids.length > 0;
    if (countEl) countEl.textContent = count + (count === 1 ? " item" : " items");
    if (totalEl) totalEl.textContent = fmt(basketTotal());
    if (checkoutBtn) checkoutBtn.disabled = count === 0;
    syncAddButtons();
  }

  // Reflect "in basket" state on the menu's Add buttons.
  function syncAddButtons() {
    document.querySelectorAll(".dish-add[data-add]").forEach(function (btn) {
      var id = btn.getAttribute("data-add");
      var n = basket[id] || 0;
      var added = n > 0;
      btn.classList.toggle("is-added", added);
      btn.textContent = added ? "Added · " + n : "Add";
    });
  }

  // One delegated click handler for Add (menu) and +/- (basket).
  document.addEventListener("click", function (e) {
    var addBtn = e.target.closest("[data-add]");
    if (addBtn) { add(addBtn.getAttribute("data-add")); return; }
    var inc = e.target.closest("[data-inc]");
    if (inc) { change(inc.getAttribute("data-inc"), 1); return; }
    var dec = e.target.closest("[data-dec]");
    if (dec) { change(dec.getAttribute("data-dec"), -1); return; }
  });

  /* ---- Checkout (demo) --------------------------------------------------- */
  var modal = document.getElementById("order-modal");
  var modalBody = document.getElementById("modal-body");
  var modalClose = document.getElementById("modal-close");
  var pickup = document.getElementById("pickup-time");

  if (checkoutBtn) {
    checkoutBtn.addEventListener("click", function () {
      if (basketCount() === 0) return;
      if (modalBody) {
        var when = pickup ? pickup.value : "shortly";
        modalBody.textContent =
          "Your order of " + basketCount() + " item" + (basketCount() === 1 ? "" : "s") +
          " (" + fmt(basketTotal()) + ") would be ready for collection — " + when.toLowerCase() + ".";
      }
      if (modal) modal.hidden = false;
    });
  }
  function closeModal() {
    if (modal) modal.hidden = true;
    basket = {};
    renderBasket();
  }
  if (modalClose) modalClose.addEventListener("click", closeModal);
  if (modal) {
    modal.addEventListener("click", function (e) { if (e.target === modal) closeModal(); });
    window.addEventListener("keydown", function (e) { if (e.key === "Escape" && !modal.hidden) closeModal(); });
  }

  /* ---- Mobile nav -------------------------------------------------------- */
  var navToggle = document.querySelector(".nav-toggle");
  var navMenu = document.getElementById("nav-links");
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = navMenu.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close after tapping a link, and when clicking away.
    navMenu.addEventListener("click", function (e) {
      if (e.target.closest("a")) navMenu.classList.remove("is-open");
    });
    document.addEventListener("click", function (e) {
      if (navMenu.classList.contains("is-open") && !e.target.closest(".nav")) {
        navMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---- Initial render ---------------------------------------------------- */
  renderCategory("coffee");
  renderBasket();
})();
