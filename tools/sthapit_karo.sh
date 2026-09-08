#!/bin/bash
# सभा को Ubuntu के menu में डालो — दर्पण एक आम app की तरह खुलेगा.
#
# कुछ system में नहीं लिखता, सब कुछ ~/.local के अंदर रहता है, इसलिए
# sudo नहीं चाहिए. हटाना हो तो: tools/sthapit_karo.sh --hatao
set -e

JAD="$(cd "$(dirname "$0")/.." && pwd)"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"
DESKTOP="$APPS/sabha.desktop"

if [ "$1" = "--hatao" ]; then
    rm -f "$DESKTOP" "$ICONS/sabha.svg"
    update-desktop-database "$APPS" 2>/dev/null || true
    echo "सभा menu से हटा दी गई."
    exit 0
fi

command -v python3 >/dev/null || { echo "python3 नहीं मिला."; exit 1; }
python3 -c "import tkinter" 2>/dev/null || {
    echo "tkinter नहीं है. पहले यह चलाओ:"
    echo "    sudo apt install python3-tk"
    exit 1
}

mkdir -p "$APPS" "$ICONS"

cat > "$ICONS/sabha.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#1d2b3a"/>
  <circle cx="32" cy="20" r="7" fill="#d9a55b"/>
  <circle cx="16" cy="42" r="6" fill="#5b8dd9"/>
  <circle cx="32" cy="46" r="6" fill="#5b8dd9"/>
  <circle cx="48" cy="42" r="6" fill="#5b8dd9"/>
  <g stroke="#5bd97e" stroke-width="2" opacity="0.75">
    <line x1="32" y1="27" x2="16" y2="36"/>
    <line x1="32" y1="27" x2="32" y2="40"/>
    <line x1="32" y1="27" x2="48" y2="36"/>
  </g>
</svg>
SVG

cat > "$DESKTOP" <<DESK
[Desktop Entry]
Type=Application
Version=1.0
Name=Sabha
Name[hi]=सभा
GenericName=AI council
GenericName[hi]=एआई सभा
Comment=Several AI members work on one task together
Comment[hi]=कई एआई सदस्य मिलकर एक काम करते हैं
Exec=python3 "$JAD/sabha.py" darpan
Path=$JAD
Icon=sabha
Terminal=false
Categories=Development;
Keywords=ai;ollama;agent;sabha;
DESK

chmod +x "$DESKTOP"
update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "सभा menu में आ गई."
echo "  entry : $DESKTOP"
echo "  चलती है: $JAD"
echo
echo "Activities खोलकर 'Sabha' या 'सभा' खोजो."
