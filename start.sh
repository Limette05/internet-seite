#!/bin/bash

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
pip3.11 install --upgrade pip
pip3.11 install flask flask_sqlalchemy flask-mail flask_login flask_wtf flask_bcrypt flask_socketio wtforms

# Überprüfen, ob die Screen-Session bereits läuft
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "Screen-Session '$SCREEN_NAME' läuft bereits. Verbinde..."
    screen -r $SCREEN_NAME
else
    echo "Starte Flask-App in einer neuen Screen-Session..."
    screen -AmdS "$SCREEN_NAME" /bin/bash -c "while true; do $PYTHON_BIN '$MAIN_SCRIPT'; echo 'Website crashed. Restarting in 10 seconds...'; sleep 10; done"
    echo "Flask-App läuft jetzt in der Screen-Session '$SCREEN_NAME'."
fi
