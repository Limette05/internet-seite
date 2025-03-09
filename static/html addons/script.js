document.addEventListener("scroll", function () {
  const navbar = document.querySelector(".menu_rectangle");
  const logo = document.querySelector(".logo-pic");

  if (window.scrollY > 150) {
    // Navbar kleiner machen
    navbar.style.height = "100px"; // Höhe der Navbar verkleinern
    // Logo ausblenden
    logo.style.opacity = "0";
    logo.style.maxHeight = "0"; // Größe des Logos auf 0 setzen
  } else {
    // Navbar wieder auf ursprüngliche Größe setzen
    navbar.style.height = "190px";
    // Logo wieder einblenden
    logo.style.opacity = "1";
    logo.style.maxHeight = "180px"; // Ursprüngliche Größe des Logos
  }
});

document.addEventListener("DOMContentLoaded", function () {
  // Funktion zum Laden von HTML-Dateien in Platzhalter
  function loadComponent(filePath, selector) {
    fetch(filePath)
      .then((response) => {
        if (!response.ok) {
          console.error("Fehler beim Laden:", filePath, response.status);
          return;
        }
        return response.text();
      })
      .then((data) => {
        const element = document.querySelector(selector);
        if (element) {
          element.innerHTML = data;
        } else {
          console.error("Platzhalter '" + selector + "' wurde nicht gefunden.");
        }
      })
      .catch((error) => {
        console.error("Fetch-Fehler:", error);
      });
  }

  // Navigation laden
  loadComponent("/static/html addons/navbar.html", ".menu_bar");

  // Kontakt laden
  loadComponent("/static/html addons/kontakt.html", ".kontakt_bar");

  // Footer laden
  loadComponent("/static/html addons/footer.html", ".footer_bar");
});

const buttonRight = document.getElementById("slideRight");
const buttonLeft = document.getElementById("slideLeft");

buttonRight.onclick = function () {
  document.getElementById("kontakt-wrapper").scrollLeft += 450;
};
buttonLeft.onclick = function () {
  document.getElementById("kontakt-wrapper").scrollLeft -= 450;
};

function loadSection(section) {
  fetch(`/${section}`)
    .then((response) => response.text())
    .then((html) => {
      document.getElementById("team-main").innerHTML = html;
    });
}
