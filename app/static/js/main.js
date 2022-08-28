function defineViewportHeight() {
  document.documentElement.style.setProperty(
    "--vh",
    window.innerHeight * 0.01 + "px"
  );
}

function defineMenuHeight() {
  const height = document.querySelector(".navbar").scrollHeight + "px";
  document.documentElement.style.setProperty("--mh", height);
}

function toggleNavbar() {
  let prevScroll = window.scrollY;
  window.onscroll = function () {
    const currentScroll = window.scrollY;
    const header = document.querySelector("header");
    if (prevScroll > currentScroll) {
      header.classList.remove("nav-hide");
    } else if (
      !document.querySelector(".nav-container").classList.contains("nav-opened")
    ) {
      header.classList.add("nav-hide");
    }
    prevScroll = currentScroll;
  };
}

function menuToggle() {
  const header = document.querySelector("header");
  const navbar = document.querySelector(".nav-container");
  const open = document.querySelector("#nav-open");
  const close = document.querySelector("#nav-close");

  open.onclick = function () {
    header.classList.remove("nav-hide");
    navbar.classList.add("nav-opened");
  };
  close.onclick = function () {
    navbar.classList.remove("nav-opened");
  };
}

function langSelector() {
  const langs = document.querySelectorAll(".lang");
  for (let i = 0; i < langs.length; i++) {
    langs[i].onclick = function (e) {
      const lang = e.target.innerText.toLowerCase();
      document.cookie = "lang=" + lang;
      location.reload();
    };
  }
}

defineViewportHeight();
defineMenuHeight();
menuToggle();
toggleNavbar();
langSelector();
