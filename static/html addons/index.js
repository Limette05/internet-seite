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

function openForm() {
  const chatFenster = document.querySelector(".messenger-container");
  chatFenster.classList.toggle("open");

  const button = document.getElementById("chatOpen");
  const isFirstClick = localStorage.getItem("buttonClicked") === null;

  button.addEventListener("click", () => {
    if (isFirstClick) {
      console.log("Erster Klick!");
      localStorage.setItem("buttonClicked", "true");
    }
  });

  const chatbox = document.getElementById("chatbox");
}

function closeForm() {
  const chatFenster = document.querySelector(".messenger-container");
  chatFenster.classList.toggle("open");
}

document.querySelectorAll(".faq-question").forEach((button) => {
  button.addEventListener("click", () => {
    const item = button.parentElement;
    const answer = item.querySelector(".faq-answer");
    const icon = button.querySelector(".faq-icon");

    if (item.classList.contains("open")) {
      answer.style.maxHeight = null;
      item.classList.remove("open");
    } else {
      document.querySelectorAll(".faq-item.open").forEach((openItem) => {
        openItem
          .querySelector(".faq-icon")
          .classList.replace("bx-x", "bx-plus");
      });

      // Dann das aktuelle öffnen
      answer.style.maxHeight = answer.scrollHeight + "px";
      item.classList.add("open");

      // Nach unten scrollen, wenn nötig
      setTimeout(() => {
        item.scrollIntoView({ behavior: "smooth", block: "end" });
      }, 500);
    }
  });
});

// Funktion zur Anzeige-/Ausblendungslogik für .cookie-item
document.querySelectorAll(".cookie-text").forEach((cookieText) => {
  cookieText.addEventListener("click", () => {
    const cookieItem = cookieText.closest(".cookie-item"); // Nur das übergeordnete .cookie-item ansprechen
    cookieItem.classList.toggle("open");

    const faqContainer = document.querySelector(".faq-container");
    const openChat = document.querySelector(".open-chat");

    if (cookieItem.classList.contains("open")) {
      faqContainer.style.display = "none";
      openChat.style.display = "none";
    } else {
      faqContainer.style.display = "block";
      openChat.style.display = "block";
    }
  });
});

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
