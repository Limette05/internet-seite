#!/bin/bash

# Name der virtuellen Umgebung
VENV_DIR="venv"

# Name der Screen-Session
SCREEN_NAME="flask_app"

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
pip install --upgrade pip
pip install flask flask_sqlalchemy flask_login flask_wtf flask_bcrypt flask_socketio wtforms

# Dateien konvertieren (nur main.py, .html, .js, .css in templates/ und static/)
for file in main.py templates/*.html static/**/*.{js,css}; do
    if [ -f "$file" ] && ! file -i "$file" | grep -q "charset=utf-8"; then
        echo "Konvertiere: $file"
        iconv -f ISO-8859-1 -t UTF-8 "$file" -o "$file.utf8" && mv "$file.utf8" "$file"
    fi
done

# Überprüfen, ob die Screen-Session bereits läuft
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "Screen-Session '$SCREEN_NAME' läuft bereits. Verbinde..."
    screen -r $SCREEN_NAME
else
    echo "Starte Flask-App in einer neuen Screen-Session..."
    screen -dmS $SCREEN_NAME bash -c "source $VENV_DIR/bin/activate && python3 main.py"
    echo "Flask-App läuft jetzt in der Screen-Session '$SCREEN_NAME'."
fi