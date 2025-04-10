document.addEventListener("scroll", function () {
  const navbar = document.querySelector(".menu_rectangle");
  const logo = document.querySelector(".logo-pic");

  if (window.scrollY > 150) {
    // Navbar kleiner machen
    navbar.style.height = "90px"; // Höhe der Navbar verkleinern
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
      document.getElementById("dashboard-display").innerHTML = html;
    });
}

window.onload = function () {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("section") === "team_chats") {
    loadSection("team_chats");
  }
};

document
  .getElementById("chatForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault(); // Verhindert das Neuladen der Seite

    const messageInput = document.getElementById("message");
    const message = messageInput.value;

    if (message.trim() === "") {
      return; // Leere Nachrichten nicht senden
    }

    // Sende die Nachricht asynchron an den Server
    const response = await fetch("/send_message", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content: message }),
    });

    const messages = await response.json();

    // Aktualisiere die Chatbox
    updateChatbox(messages);

    // Leert das Eingabefeld
    messageInput.value = "";
  });

function updateChatbox(messages) {
  const chatbox = document.getElementById("chatbox");
  chatbox.innerHTML = ""; // Leert die Chatbox (optional)

  // Neue Nachrichten hinzufügen
  messages.forEach((msg) => {
    const messageElement = document.createElement("div");
    messageElement.className =
      msg.username === "{{ username }}"
        ? "messenger-msg-right"
        : "messenger-msg-left";
    messageElement.innerHTML = `
            <div style="font-size: 16px;"><b>${msg.username}</b></div>
            <div style="font-size: 14px;">${msg.content}</div>
            <span style="font-size: 12px; color: rgba(245, 245, 245, 0.75);">${msg.created_at}</span>
        `;
    chatbox.appendChild(messageElement);
  });

  // Scrollt die Chatbox zum neuesten Eintrag
  chatbox.scrollTop = chatbox.scrollHeight;
}

function searchAdvertisements() {
  var input, filter, ul, li, a, i, txtValue;
  input = document.getElementById("searchAdvertisements");
  filter = input.value.toUpperCase();
  ul = document.getElementById("werbungList");
  li = ul.getElementsByTagName("div");
  for (i = 0; i < li.length; i++) {
    a = li[i].getElementsByTagName("button")[0];
    txtValue = a.textContent || a.innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      li[i].style.display = "flex";
    } else {
      li[i].style.display = "none";
    }
  }
}

function redirectToAd(adID) {
  window.location.href = `/werbung?werbung_ID=${adID}`;
}

const input = document.getElementById("werbung-image");
const preview = document.getElementById("werbung-image-preview");

input.addEventListener("change", function () {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      preview.src = e.target.result; // Vorschau anzeigen
    };
    reader.readAsDataURL(file); // Lokale Datei als Base64 laden
  }
});

function searchUser() {
  var input, filter, ul, li, a, i, txtValue;
  input = document.getElementById("searchUser");
  filter = input.value.toUpperCase();
  ul = document.getElementById("userList");
  li = ul.getElementsByTagName("div");
  for (i = 0; i < li.length; i++) {
    a = li[i].getElementsByTagName("button")[0];
    txtValue = a.textContent || a.innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      li[i].style.display = "flex";
    } else {
      li[i].style.display = "none";
    }
  }
}

function redirectToUser(userID) {
  window.location.href = `/admin?userID=${userID}`;
}