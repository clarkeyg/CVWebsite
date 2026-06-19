/* OptiFuelUK — marketing site behaviour
   Mobile nav: toggle the menu open/closed and keep aria-expanded in sync. */
(function () {
  var burgers = document.querySelectorAll('.nav-burger');
  burgers.forEach(function (burger) {
    var menu = document.getElementById(burger.getAttribute('aria-controls'));
    if (!menu) return;

    burger.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', String(open));
    });

    // Close the menu after following an in-menu link.
    menu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        menu.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      });
    });
  });
})();
