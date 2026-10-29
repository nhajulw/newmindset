// Language switch (Khmer / English, remembered on this device) and the tap-to-play video.
(function () {
  var post = document.querySelector(".post");
  if (post) {
    var key = "nm-lang", lang = "km";
    try { lang = localStorage.getItem(key) || "km"; } catch (e) {}
    var set = function (l) {
      post.classList.toggle("show-km", l === "km");
      post.classList.toggle("show-en", l === "en");
      document.querySelectorAll(".lang-switch button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.lang === l)); });
      try { localStorage.setItem(key, l); } catch (e) {}
    };
    document.querySelectorAll(".lang-switch button").forEach(function (b) {
      b.addEventListener("click", function () { set(b.dataset.lang); });
    });
    set(lang);
  }
  // The YouTube player loads only when tapped (lighter pages on phones); without JS the link opens YouTube.
  document.querySelectorAll(".yt-lite").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(a.dataset.id) + "?autoplay=1&playsinline=1&rel=0";
      f.title = a.getAttribute("aria-label") || "Video";
      f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      f.allowFullscreen = true;
      a.replaceWith(f);
    });
  });
})();
