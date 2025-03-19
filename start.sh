#!/bin/bash

# Ins richtige Verzeichnis wechseln
cd internet-seite/ || { echo "Verzeichnis internet-seite/ nicht gefunden!"; exit 1; }

# Datei definieren
DATEI="main.py"

# Änderungen vornehmen
sed -i "20s|.*|host = 'your host'|" "$DATEI"
sed -i "27s|.*|app.config['MAIL_USERNAME'] = 'noreply.your@email.com'|" "$DATEI"
sed -i "28s|.*|app.config['MAIL_PASSWORD'] = 'your app password'|" "$DATEI"

echo "main.py wurde aktualisiert."

# Name der virtuellen Umgebung
VENV_DIR="venv"

# Name der Screen-Session
SCREEN_NAME="flask_app"

MAIN_SCRIPT="main.py"

# Python-Version
PYTHON_BIN="/usr/local/bin/python3.11"

# Überprüfen, ob screen installiert ist
if ! command -v screen &> /dev/null; then
    echo "Error: screen ist nicht installiert. Bitte installiere es mit 'sudo apt-get install screen'"
    exit 1
fi

# Virtuelle Umgebung erstellen, falls sie nicht existiert
if [ ! -d "$VENV_DIR" ]; then
    echo "Erstelle virtuelle Umgebung..."
    python3 -m venv $VENV_DIR
fi

# Aktivieren der virtuellen Umgebung
source $VENV_DIR/bin/activate

# Installieren der Abhängigkeiten
<<<<<<< HEAD
pip3.11 install --upgrade pip
pip3.11 install flask flask_sqlalchemy flask-mail flask_login flask_wtf flask_bcrypt flask_socketio wtforms
=======
pip install --upgrade pip
pip install flask flask_sqlalchemy flask-mail flask_login flask_wtf flask_bcrypt flask_socketio wtforms
>>>>>>> dc5f9e567879b9b17ab9678d7f8c45e0d8af9e9f

# Überprüfen, ob die Screen-Session bereits läuft
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "Screen-Session '$SCREEN_NAME' läuft bereits. Verbinde..."
    screen -r $SCREEN_NAME
else
    echo "Starte Flask-App in einer neuen Screen-Session..."
    screen -AmdS "$SCREEN_NAME" /bin/bash -c "while true; do $PYTHON_BIN '$MAIN_SCRIPT'; echo 'Website crashed. Restarting in 10 seconds...'; sleep 10; done"
    echo "Flask-App läuft jetzt in der Screen-Session '$SCREEN_NAME'."
fi
