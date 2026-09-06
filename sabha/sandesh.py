# -*- coding: utf-8 -*-
"""
संदेश (SANDESH) — सदस्यों के बीच बात कराने वाला डाकख़ाना.

यह क्या है:
    हर सदस्य का अपना डिब्बा है. वो अपनी बात 'bahar' में रख देता है.
    डाकिया (router) उसे उठाकर पाने वाले के 'andar' में डाल देता है.

यह ऐसा क्यों — यहाँ Redis या RabbitMQ क्यों नहीं:
    तीन वजहें, और तीनों दो-तीन साल वाली शर्त से निकली हैं.

    पहली — कुछ install नहीं करना. Redis चलाने का मतलब है एक और service
    जो चालू रखनी पड़े, जिसका version बदले, जो किसी दिन बूट पर न उठे.
    यहाँ सिर्फ़ files हैं. Files दो साल बाद भी files रहेंगी.

    दूसरी — देखा जा सकता है. कुछ गड़बड़ हो तो तुम folder खोलकर पढ़ सकते हो
    कि किसने किससे क्या कहा. Redis में वही देखने के लिए अलग tool चाहिए.
    जब तीन बजे रात को कुछ अटका हो, तब यह बहुत मायने रखता है.

    तीसरी — मरने पर बचा रहता है. Process मर जाए, बिजली चली जाए — संदेश
    disk पर पड़े रहेंगे. अगली बार वहीं से काम शुरू होगा.

एक ज़रूरी नियम — लिखने वाला अकेला:
    कोई भी सदस्य सीधे किसी दूसरे के डिब्बे में नहीं लिखता. सब अपने 'bahar'
    में लिखते हैं, और डाकिया अकेला उठाकर बाँटता है.

    ऐसा इसलिए कि दो सदस्य एक ही वक़्त एक ही file पर लिखें तो file अधूरी
    लिखी जा सकती है. एक ही लिखने वाला हो तो यह समस्या पैदा ही नहीं होती —
    ताला (lock) लगाने की ज़रूरत ही नहीं पड़ती.

यह कहाँ जाता है:
    sabhapati.py डाकिया चलाता है,
    sadasya.py अपने डिब्बे से पढ़ता-लिखता है.
"""

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

# संदेश के प्रकार — एक जगह रखे हैं ताकि spelling की ग़लती न हो
KAAM = "kaam"              # सभापति -> सदस्य : यह काम करो
NATIJA = "natija"          # सदस्य -> सभापति : काम हो गया, यह नतीजा है
ATKA = "atka"              # सदस्य -> सभापति : अटक गया, मदद चाहिए
PUCHHO = "puchho"          # सदस्य -> सदस्य   : यह बताओ
SOOCHNA = "soochna"        # किसी के लिए भी  : जानकारी


class Sandesh(object):
    """एक संदेश. सादा dict ही है, पर नाम वाले खाने तय हैं."""

    def __init__(self, se, ko, prakar, vishay, samagri=None, sutra=None):
        """
        se      = किससे आया (सदस्य का नाम)
        ko      = किसे जाना है
        prakar  = ऊपर वाले प्रकारों में से एक
        vishay  = एक लाइन में बात
        samagri = पूरा ब्योरा (कुछ भी, JSON में जाने लायक)
        sutra   = किस काम से जुड़ा है (task id) — इसी से धागा जुड़ा रहता है
        """
        self.id = uuid.uuid4().hex[:12]
        self.se = se
        self.ko = ko
        self.prakar = prakar
        self.vishay = vishay
        self.samagri = samagri if samagri is not None else {}
        self.sutra = sutra
        self.samay = time.time()

    def dict_me(self):
        return {
            "id": self.id, "se": self.se, "ko": self.ko,
            "prakar": self.prakar, "vishay": self.vishay,
            "samagri": self.samagri, "sutra": self.sutra,
            "samay": self.samay,
        }

    @staticmethod
    def dict_se(d):
        s = Sandesh(d.get("se", "?"), d.get("ko", "?"),
                    d.get("prakar", SOOCHNA), d.get("vishay", ""),
                    d.get("samagri"), d.get("sutra"))
        s.id = d.get("id", s.id)
        s.samay = d.get("samay", s.samay)
        return s

    def __repr__(self):
        return "<%s %s->%s: %s>" % (self.prakar, self.se, self.ko, self.vishay)


class Dakkhana(object):
    """
    डाकख़ाना — सारे डिब्बे और डाकिया, दोनों यहीं.

    Folder की शक्ल:
        sabha-kaksh/
            <सदस्य>/
                andar/     <- इसके लिए आए संदेश
                bahar/     <- इसने भेजे संदेश, बँटने का इंतज़ार
                hua/       <- बँट चुके (कुछ दिन बाद मिट जाते हैं)
    """

    def __init__(self, kaksh):
        """kaksh = sabha-kaksh folder का रास्ता."""
        self.kaksh = kaksh
        os.makedirs(self.kaksh, exist_ok=True)

    # -- डिब्बे --------------------------------------------------------------

    def dibba_banao(self, sadasya):
        """एक सदस्य के तीनों folder बनाता है. दोबारा चलाने पर कुछ नहीं बिगड़ता."""
        for kya in ("andar", "bahar", "hua"):
            os.makedirs(os.path.join(self.kaksh, sadasya, kya), exist_ok=True)

    def _rasta(self, sadasya, kya):
        return os.path.join(self.kaksh, sadasya, kya)

    # -- लिखना ---------------------------------------------------------------

    def bhejo(self, sandesh):
        """
        संदेश भेजने वाले के 'bahar' में रखता है. यहाँ से डाकिया उठाएगा.

        File का नाम समय + id से बनता है. समय पहले इसलिए कि नाम से क्रम
        अपने आप सही बन जाए — sorted() ही काफ़ी है, अलग से क्रम नहीं लगाना पड़ता.
        """
        self.dibba_banao(sandesh.se)
        naam = "%.6f_%s.json" % (sandesh.samay, sandesh.id)
        rasta = os.path.join(self._rasta(sandesh.se, "bahar"), naam)

        # पहले .tmp में, फिर rename — बिजली जाने पर आधा संदेश न बचे
        temp = rasta + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(sandesh.dict_me(), f, ensure_ascii=False, indent=2)
        os.rename(temp, rasta)
        return sandesh.id

    # -- डाकिया ---------------------------------------------------------------

    def baanto(self):
        """
        सारे 'bahar' डिब्बे देखता है और संदेशों को उनके पते पर पहुँचाता है.

        यह अकेला function है जो दूसरों के 'andar' में लिखता है. बाक़ी पूरा
        system सिर्फ़ अपने ही डिब्बे को छूता है. इसीलिए किसी ताले की
        ज़रूरत नहीं पड़ती.

        लौटाता है: कितने संदेश बँटे.
        """
        bante = 0
        if not os.path.isdir(self.kaksh):
            return 0

        for sadasya in sorted(os.listdir(self.kaksh)):
            bahar = self._rasta(sadasya, "bahar")
            if not os.path.isdir(bahar):
                continue

            for f in sorted(os.listdir(bahar)):
                if not f.endswith(".json"):
                    continue          # .tmp वाले छोड़ो, वो अभी लिखे जा रहे हैं

                poora = os.path.join(bahar, f)
                try:
                    with open(poora, "r", encoding="utf-8") as fh:
                        d = json.load(fh)
                except (ValueError, IOError, OSError):
                    # ख़राब संदेश पूरा डाकख़ाना न रोके — किनारे रख दो
                    self._kinare_rakho(poora)
                    continue

                ko = d.get("ko", "")
                if not ko:
                    self._kinare_rakho(poora)
                    continue

                # 'sab' का मतलब सबको (सभापति को छोड़कर, वरना गूँज बनेगी)
                pane_wale = [ko]
                if ko == "sab":
                    pane_wale = [s for s in os.listdir(self.kaksh)
                                 if s != sadasya and
                                 os.path.isdir(os.path.join(self.kaksh, s))]

                for p in pane_wale:
                    self.dibba_banao(p)
                    naya = os.path.join(self._rasta(p, "andar"), f)
                    with open(naya, "w", encoding="utf-8") as fh:
                        json.dump(d, fh, ensure_ascii=False, indent=2)

                # बँटने के बाद 'hua' में सरका दो — इतिहास बना रहे
                os.rename(poora, os.path.join(self._rasta(sadasya, "hua"), f))
                bante += 1

        return bante

    def _kinare_rakho(self, rasta):
        """ख़राब संदेश को .kharab बनाकर छोड़ देता है, ताकि वो बार-बार न अटकाए."""
        try:
            os.rename(rasta, rasta + ".kharab")
        except OSError:
            pass

    # -- पढ़ना ----------------------------------------------------------------

    def padho(self, sadasya, hatao=True):
        """
        एक सदस्य के 'andar' के सारे संदेश लौटाता है, क्रम में.

        hatao=True (default) पढ़ने के बाद उन्हें हटा देता है — यही सामान्य
        बर्ताव है, वरना वही संदेश बार-बार पढ़े जाएँगे.
        hatao=False झाँकने के लिए है, जब सिर्फ़ देखना हो.
        """
        andar = self._rasta(sadasya, "andar")
        if not os.path.isdir(andar):
            return []

        mile = []
        for f in sorted(os.listdir(andar)):
            if not f.endswith(".json"):
                continue
            poora = os.path.join(andar, f)
            try:
                with open(poora, "r", encoding="utf-8") as fh:
                    mile.append(Sandesh.dict_se(json.load(fh)))
            except (ValueError, IOError, OSError):
                self._kinare_rakho(poora)
                continue
            if hatao:
                try:
                    os.remove(poora)
                except OSError:
                    pass
        return mile

    def kitne_pade_hain(self, sadasya):
        """बिना पढ़े गिनती — सभापति यह देखकर तय करता है कि किसे काम देना है."""
        andar = self._rasta(sadasya, "andar")
        if not os.path.isdir(andar):
            return 0
        return len([f for f in os.listdir(andar) if f.endswith(".json")])

    # -- सफ़ाई ----------------------------------------------------------------

    def safai(self, din=7):
        """
        'hua' folder में पड़े पुराने संदेश मिटाता है.

        मंडल वाला वही नियम — बाहरी परत अपने आप ख़त्म होती है. बिना इसके
        छह महीने में यह folder लाखों छोटी files से भर जाएगा, और उसके बाद
        हर listing धीमी हो जाएगी.
        """
        seema = din * 24 * 60 * 60
        ab = time.time()
        mite = 0
        if not os.path.isdir(self.kaksh):
            return 0
        for sadasya in os.listdir(self.kaksh):
            hua = self._rasta(sadasya, "hua")
            if not os.path.isdir(hua):
                continue
            for f in os.listdir(hua):
                poora = os.path.join(hua, f)
                try:
                    if ab - os.path.getmtime(poora) > seema:
                        os.remove(poora)
                        mite += 1
                except OSError:
                    pass
        return mite


# ---------------------------------------------------------------------------
# जाँच: python3 sabha/sandesh.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile

    d = Dakkhana(tempfile.mkdtemp())
    d.dibba_banao("sabhapati")
    d.dibba_banao("ved-1")
    d.dibba_banao("ved-2")

    d.bhejo(Sandesh("sabhapati", "ved-1", KAAM, "यह काम करो",
                    {"kya": "गिनती करो"}, sutra="k1"))
    assert d.kitne_pade_hain("ved-1") == 0, "बाँटने से पहले ही पहुँच गया?"

    bante = d.baanto()
    assert bante == 1, "बँटा नहीं"
    assert d.kitne_pade_hain("ved-1") == 1

    mile = d.padho("ved-1")
    assert len(mile) == 1 and mile[0].vishay == "यह काम करो"
    assert d.kitne_pade_hain("ved-1") == 0, "पढ़ने के बाद हटा नहीं"

    # सबको भेजना
    d.bhejo(Sandesh("sabhapati", "sab", SOOCHNA, "सब सुनो"))
    d.baanto()
    assert d.kitne_pade_hain("ved-1") == 1
    assert d.kitne_pade_hain("ved-2") == 1
    assert d.kitne_pade_hain("sabhapati") == 0, "भेजने वाले को अपनी ही बात मिली"

    print("डाकख़ाना ठीक है — सारी जाँच पास.")
