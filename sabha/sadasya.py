# -*- coding: utf-8 -*-
"""
सदस्य (SADASYA) — सभा का वो सदस्य जो असल में काम करता है.

यह क्या है:
    एक सदस्य = एक दिमाग़ + एक डिब्बा + एक बजट.

    तीन तरह के दिमाग़ चलते हैं:
        ollama : तुम्हारी अपनी मशीन पर चलता local model (HTTP से)
        aujaar : कोई CLI agent — claude, gemini, codex (subprocess से)
        nakli  : नक़ली, जाँच के लिए (कुछ चलाता ही नहीं)

यह ऐसा क्यों — तीनों एक ही ढाँचे में क्यों:
    सभापति को यह जानने की ज़रूरत नहीं होनी चाहिए कि सदस्य के अंदर क्या है.
    उसे बस 'काम दो, जवाब लो' आना चाहिए.

    इससे दो फ़ायदे हैं. पहला — तुम आज ollama पर चलाओ, कल किसी CLI पर,
    बाक़ी system में एक लाइन नहीं बदलेगी. दूसरा, और ज़्यादा ज़रूरी —
    'nakli' सदस्य की वजह से पूरा system बिना Ollama, बिना internet, बिना
    किसी API key के जाँचा जा सकता है.

    वो दूसरी बात दो-तीन साल वाली शर्त के लिए सबसे अहम है. जिस system की
    जाँच के लिए बाहरी service चाहिए, उसकी जाँच धीरे-धीरे होनी बंद हो
    जाती है — और फिर वो चुपचाप टूट जाता है.

यह कहाँ जुड़ता है:
    sabhapati.py इन्हें बनाता और चलाता है,
    raksha.py इनका ख़र्च गिनता है,
    sandesh.py इनका डाकख़ाना है.
"""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

# Ollama अपनी मशीन पर यहीं बैठता है
OLLAMA_PATA = "http://127.0.0.1:11434"


class Sadasya(object):
    """सभा का एक सदस्य."""

    def __init__(self, naam, prakar, model=None, hukum=None,
                 kaam_ka_vivaran="", samay_seema=300):
        """
        naam            = सदस्य का नाम, जैसे 'ved-1'
        prakar          = 'ollama' | 'aujaar' | 'nakli'
        model           = ollama के लिए model का नाम
        hukum           = aujaar के लिए हुक्म की सूची, जैसे ['claude','-p']
        kaam_ka_vivaran = यह सदस्य किस काम में माहिर है (सभापति इसी से चुनता है)
        samay_seema     = कितनी देर इंतज़ार करें
        """
        self.naam = naam
        self.prakar = prakar
        self.model = model
        self.hukum = hukum or []
        self.kaam_ka_vivaran = kaam_ka_vivaran
        self.samay_seema = samay_seema

        # नक़ली सदस्य के लिए — जाँच में क्या लौटाना है
        self.nakli_jawab = []
        self.nakli_ginti = 0

    # -- मुख्य काम -------------------------------------------------------------

    def poochho(self, sawal, sandarbh=""):
        """
        सदस्य से एक सवाल पूछता है और जवाब लौटाता है.

        लौटाता है dict:
            {"jawab": …, "akshar": …, "second": …, "safal": True/False,
             "galti": …}

        कभी exception नहीं फेंकता. वजह — एक सदस्य के गिरने से पूरी सभा
        नहीं गिरनी चाहिए. गड़बड़ होने पर safal=False लौटता है और सभापति
        तय करता है कि आगे क्या करना है.
        """
        shuru = time.time()
        poora_sawal = (sandarbh + "\n\n" + sawal) if sandarbh else sawal

        try:
            if self.prakar == "ollama":
                jawab = self._ollama_se(poora_sawal)
            elif self.prakar == "aujaar":
                jawab = self._aujaar_se(poora_sawal)
            elif self.prakar == "nakli":
                jawab = self._nakli_se(poora_sawal)
            else:
                return self._galti("अनजान प्रकार: " + str(self.prakar), shuru)
        except Exception as e:
            return self._galti("%s: %s" % (type(e).__name__, str(e)), shuru)

        lага = time.time() - shuru
        return {
            "jawab": jawab,
            # अक्षरों से token का अंदाज़ा — चार अक्षर लगभग एक token.
            # पक्की गिनती के लिए tokenizer चाहिए, जो एक और dependency होती.
            # बजट के लिए अंदाज़ा काफ़ी है, क्योंकि हमें सिर्फ़ यह जानना है
            # कि कोई सदस्य हद से बाहर तो नहीं जा रहा.
            "akshar": (len(poora_sawal) + len(jawab)) // 4,
            "second": lага,
            "safal": True,
            "galti": "",
        }

    def _galti(self, sandesh, shuru):
        return {
            "jawab": "", "akshar": 0, "second": time.time() - shuru,
            "safal": False, "galti": sandesh,
        }

    # -- तीन दिमाग़ --------------------------------------------------------------

    def _ollama_se(self, sawal):
        """
        Ollama से जवाब लेता है, सादे HTTP से.

        यहाँ requests library जान-बूझकर नहीं इस्तेमाल की — urllib stdlib
        में है, और यही पूरी बात है. एक pip package कम, एक टूटने की जगह कम.
        """
        data = json.dumps({
            "model": self.model,
            "prompt": sawal,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_PATA + "/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.samay_seema) as r:
            jawab = json.loads(r.read().decode("utf-8"))
        return jawab.get("response", "")

    def _aujaar_se(self, sawal):
        """
        किसी CLI agent को चलाकर जवाब लेता है.

        सवाल stdin से भेजा जाता है, हुक्म-लाइन में नहीं. वजह: लंबा सवाल
        हुक्म-लाइन की सीमा से बड़ा हो सकता है, और उसमें quote/escape का
        झंझट अलग से बनता है. stdin में यह दोनों समस्याएँ हैं ही नहीं.
        """
        p = subprocess.run(
            self.hukum,
            input=sawal,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.samay_seema,
            encoding="utf-8",
            errors="replace",
        )
        if p.returncode != 0 and not (p.stdout or "").strip():
            raise RuntimeError((p.stderr or "").strip()[:400])
        return p.stdout or ""

    def _nakli_se(self, sawal):
        """
        नक़ली जवाब — जाँच के लिए. कुछ चलाता नहीं.

        nakli_jawab में जो सूची रखी है, उसमें से एक-एक करके लौटाता है.
        सूची ख़त्म हो जाए तो आख़िरी वाला दोहराता रहता है — इससे 'अटका हुआ
        सदस्य' वाली स्थिति बनाकर लगाम की जाँच की जा सकती है.
        """
        if not self.nakli_jawab:
            return "नक़ली जवाब: " + sawal[:60]
        i = min(self.nakli_ginti, len(self.nakli_jawab) - 1)
        self.nakli_ginti += 1
        return self.nakli_jawab[i]

    # -- ज़िंदा है या नहीं ---------------------------------------------------------

    def zinda_hai(self):
        """
        यह सदस्य अभी काम कर सकता है या नहीं.

        सभा शुरू करने से पहले यह पूछा जाता है. वजह — दस मिनट काम चलाने के
        बाद पता चले कि Ollama बंद था, यह सबसे चिढ़ाने वाली बात होती है.
        पहले ही जाँच लो.
        """
        if self.prakar == "nakli":
            return True, ""

        if self.prakar == "ollama":
            try:
                with urllib.request.urlopen(OLLAMA_PATA + "/api/tags",
                                            timeout=5) as r:
                    d = json.loads(r.read().decode("utf-8"))
                maujood = [m.get("name", "") for m in d.get("models", [])]
                # 'llama3.1:8b' और 'llama3.1' दोनों चलें
                for m in maujood:
                    if m == self.model or m.split(":")[0] == self.model:
                        return True, ""
                return False, "model '%s' Ollama में नहीं है (मिले: %s)" % (
                    self.model, ", ".join(maujood[:5]) or "कोई नहीं")
            except Exception as e:
                return False, "Ollama से बात नहीं हुई: %s" % str(e)[:120]

        if self.prakar == "aujaar":
            if not self.hukum:
                return False, "कोई हुक्म नहीं दिया"
            import shutil
            if shutil.which(self.hukum[0]) is None:
                return False, "'%s' मशीन पर मिला नहीं" % self.hukum[0]
            return True, ""

        return False, "अनजान प्रकार"

    def haal(self):
        return {"naam": self.naam, "prakar": self.prakar,
                "model": self.model, "kaam": self.kaam_ka_vivaran}

    def __repr__(self):
        return "<सदस्य %s (%s)>" % (self.naam, self.prakar)


# ---------------------------------------------------------------------------
# जाँच: python3 sabha/sadasya.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    s = Sadasya("nakli-1", "nakli", kaam_ka_vivaran="जाँच के लिए")
    s.nakli_jawab = ["पहला जवाब", "दूसरा जवाब"]

    zinda, _ = s.zinda_hai()
    assert zinda is True

    r1 = s.poochho("कुछ करो")
    assert r1["safal"] and r1["jawab"] == "पहला जवाब", r1
    r2 = s.poochho("और करो")
    assert r2["jawab"] == "दूसरा जवाब"
    r3 = s.poochho("फिर करो")
    assert r3["jawab"] == "दूसरा जवाब", "सूची ख़त्म होने पर आख़िरी दोहराना चाहिए"
    assert r1["akshar"] > 0, "अक्षर गिने नहीं गए"

    # ग़लत प्रकार पर crash नहीं, safal=False
    b = Sadasya("bura", "kuchh-aur")
    r = b.poochho("x")
    assert r["safal"] is False and "अनजान" in r["galti"]

    # Ollama है या नहीं — जाँच सिर्फ़ बताती है, रोकती नहीं
    o = Sadasya("ved-1", "ollama", model="llama3.1:8b")
    zinda, vajah = o.zinda_hai()
    print("Ollama:", "मिला" if zinda else "नहीं — " + vajah)

    # CLI aujaar
    a = Sadasya("aujaar-1", "aujaar", hukum=["cat"])
    zinda, vajah = a.zinda_hai()
    assert zinda, vajah
    r = a.poochho("नमस्ते सभा")
    assert "नमस्ते सभा" in r["jawab"], r

    print("सदस्य ठीक है — सारी जाँच पास.")
