#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
सभा (SABHA) — कई AI सदस्यों की एक सभा, जो मिलकर एक काम करते हैं.

चलाने के तरीक़े:

    python3 sabha.py jaancho
        सिर्फ़ देखो कि कौन सदस्य ज़िंदा है. कुछ चलाता नहीं.
        हर बार काम शुरू करने से पहले यही चलाओ.

    python3 sabha.py chalao "काम यहाँ लिखो"
        सभा बुलाओ. काम अपने आप बँटेगा और सदस्यों में बँट जाएगा.

    python3 sabha.py chalao "काम" --tukde "क" "ख" "ग"
        तुम ख़ुद बाँटकर दो. तब सभापति बँटवाने में समय नहीं लगाएगा.

    python3 sabha.py hisaab
        पिछली सभाओं का हिसाब — किसने कितना काम किया, कितना ख़र्च हुआ.

    python3 sabha.py nakli
        नक़ली सदस्यों से पूरी सभा चलाकर देखो. कुछ install किए बिना,
        बिना Ollama के. यह जाँचने के लिए कि तंत्र ठीक है.

बनाने वाला: कनक प्रभाकर
"""

import argparse
import json
import os
import sys

YAHAN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(YAHAN, "sabha"))

from sadasya import Sadasya                                  # noqa: E402
from sabhapati import Sabhapati                              # noqa: E402
from nireekshan import Nireekshak                            # noqa: E402


def niyukti_padho(rasta=None):
    """niyukti.json पढ़कर सदस्य बनाता है."""
    rasta = rasta or os.path.join(YAHAN, "niyukti.json")
    if not os.path.exists(rasta):
        print("niyukti.json नहीं मिली:", rasta)
        sys.exit(1)
    with open(rasta, "r", encoding="utf-8") as f:
        d = json.load(f)

    sadasya = []
    for s in d.get("sadasya", []):
        if not s.get("chalu", True):
            continue          # बंद सदस्य छोड़ दो
        sadasya.append(Sadasya(
            naam=s["naam"],
            prakar=s["prakar"],
            model=s.get("model"),
            hukum=s.get("hukum"),
            kaam_ka_vivaran=s.get("kaam_ka_vivaran", ""),
            samay_seema=s.get("samay_seema", 300),
        ))
    return sadasya, d


def budget_lagao(sp, d):
    """niyukti.json के बजट सभापति पर लगाता है."""
    for s in d.get("sadasya", []):
        if s.get("chalu", True) and s["naam"] in sp.sadasya:
            sp.raksha.budget_do(
                s["naam"],
                s.get("adhiktam_akshar", 200000),
                s.get("adhiktam_second", 1800))


def hukum_jaancho():
    """कौन सदस्य ज़िंदा है."""
    sadasya, d = niyukti_padho()
    if not sadasya:
        print("कोई सदस्य चालू नहीं है. niyukti.json में 'chalu': true करो.")
        return 1

    print()
    print("  सदस्यों की जाँच")
    print("  " + "-" * 58)
    kitne_theek = 0
    for s in sadasya:
        zinda, vajah = s.zinda_hai()
        if zinda:
            print("  [ ठीक ]  %-16s %-10s %s" % (
                s.naam, s.prakar, s.model or " ".join(s.hukum)))
            kitne_theek += 1
        else:
            print("  [ नहीं ]  %-16s %s" % (s.naam, vajah))
    print()
    print("  %d में से %d सदस्य तैयार." % (len(sadasya), kitne_theek))
    if kitne_theek == 0:
        print()
        print("  कोई तैयार नहीं. आम वजहें:")
        print("    - Ollama चल नहीं रहा   ->  ollama serve")
        print("    - model उतरा नहीं      ->  ollama pull <नाम>")
        print("    - CLI मशीन पर नहीं है  ->  niyukti.json में chalu:false करो")
        return 1
    print()
    return 0


def sabha_banao():
    """niyukti.json पढ़कर एक तैयार Sabhapati देता है.

    chalao और darpan दोनों यही बुलाते हैं, ताकि खिड़की और CLI कभी अलग
    तरीक़े से सभा न बनाएँ.
    """
    sadasya, d = niyukti_padho()
    if not sadasya:
        raise RuntimeError("कोई सदस्य चालू नहीं है.")

    cfg = d.get("sabha", {})
    sp = Sabhapati(
        YAHAN, sadasya,
        adhiktam_gehrai=cfg.get("adhiktam_gehrai", 3),
        adhiktam_kaam=cfg.get("adhiktam_kaam", 200),
        apne_aap_manzoori=cfg.get("apne_aap_manzoori", False),
    )
    budget_lagao(sp, d)
    return sp


def hukum_darpan():
    """दर्पण — सभा की खिड़की."""
    from darpan import kholo
    try:
        kholo(sabha_banao)
    except RuntimeError as e:
        print(e)
        return 1
    return 0


def hukum_chalao(kaam, tukde=None, chakkar=None):
    """सभा बुलाओ."""
    try:
        sp = sabha_banao()
    except RuntimeError as e:
        print(e)
        return 1

    theek, gadbad = sp.sadasya_jaancho()
    if gadbad:
        print()
        for naam, vajah in gadbad:
            print("  [ध्यान] %s तैयार नहीं — %s" % (naam, vajah))
        # जो तैयार नहीं, उन्हें रोक दो — वरना हर काम उन पर जाकर नाकाम होगा
        for naam, _ in gadbad:
            sp.ruke_hue.add(naam)
    if not theek:
        print("\n  कोई सदस्य तैयार नहीं. पहले 'jaancho' चलाओ.\n")
        return 1

    print()
    print("  काम: " + kaam)
    print("  सदस्य: " + ", ".join(theek))
    print("  " + "-" * 58)

    sp.kaam_lo(kaam, tukde=tukde)
    sp.chalao(adhiktam_chakkar=chakkar or cfg.get("adhiktam_chakkar", 100))
    sp.haal_chhapo()

    jawab = sp.jawab_banao()
    out = os.path.join(YAHAN, "jawab.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# " + kaam + "\n\n" + jawab)
    print()
    print("  जवाब लिखा गया:", out)
    print("  बही-खाता:", os.path.join(YAHAN, "bahi", "sabha.jsonl"))
    print()
    sp.band()
    return 0


def hukum_hisaab():
    """पिछली सभाओं का हिसाब."""
    n = Nireekshak(os.path.join(YAHAN, "bahi"))
    h = n.hisaab()
    if not h:
        print("\n  अभी कोई हिसाब नहीं — पहले कोई सभा चलाओ.\n")
        return 0

    print()
    print("  %-16s %8s %10s %8s %8s" % (
        "सदस्य", "काम", "अक्षर", "सेकंड", "नाकाम"))
    print("  " + "-" * 56)
    for kaun in sorted(h):
        v = h[kaun]
        if v["kaam"] == 0:
            continue
        print("  %-16s %8d %10d %8.1f %8d" % (
            kaun, v["kaam"], v["akshar"], v["second"], v["nakaam"]))
    print()
    print("  यह हिसाब इसलिए रखा जाता है कि तुम देख सको कि सदस्य बढ़ाने से")
    print("  नतीजा सचमुच बेहतर होता है या सिर्फ़ ख़र्च बढ़ता है.")
    print()
    n.band()
    return 0


def hukum_nakli():
    """नक़ली सदस्यों से पूरी सभा चलाकर दिखाओ."""
    print()
    print("  नक़ली सभा — कुछ install किए बिना, बिना Ollama के.")
    print("  यह देखने के लिए कि तंत्र ठीक चल रहा है.")
    print("  " + "-" * 58)

    a = Sadasya("nakli-1", "nakli", kaam_ka_vivaran="खोज")
    a.nakli_jawab = [
        "- पहला हिस्सा: पुराने आँकड़े इकट्ठे करो\n"
        "- दूसरा हिस्सा: अभी की हालत देखो\n"
        "- तीसरा हिस्सा: दोनों की तुलना करो",
        "पहले हिस्से का जवाब — पुराने आँकड़े यहाँ इकट्ठे किए गए हैं, "
        "और उनसे यह पता चलता है कि पिछले सालों में क्या हुआ.",
        "तीसरे हिस्से का जवाब — दोनों की तुलना से यह निकलता है कि "
        "बदलाव किस दिशा में गया और कितना.",
    ]
    b = Sadasya("nakli-2", "nakli", kaam_ka_vivaran="लिखाई")
    b.nakli_jawab = [
        "दूसरे हिस्से का जवाब — अभी की हालत यह है, और इसमें ये बातें "
        "ख़ास तौर पर ध्यान देने लायक हैं.",
        "आख़िरी जोड़ — तीनों हिस्सों को मिलाकर यह पूरी तस्वीर बनती है.",
    ]

    sp = Sabhapati(YAHAN, [a, b])
    sp.kaam_lo("जाँच का काम — यह सिर्फ़ दिखाने के लिए है")
    sp.chalao(adhiktam_chakkar=20)
    sp.haal_chhapo()
    print()
    print("  अगर ऊपर काम पूरे हुए दिख रहे हैं, तो तंत्र ठीक है.")
    print("  अब niyukti.json में असली सदस्य चालू करो.")
    print()
    sp.band()
    return 0


def mukhya():
    p = argparse.ArgumentParser(
        description="सभा — कई AI सदस्यों की एक सभा",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    up = p.add_subparsers(dest="hukum")

    up.add_parser("jaancho", help="कौन सदस्य ज़िंदा है")

    c = up.add_parser("chalao", help="सभा बुलाओ")
    c.add_argument("kaam", help="क्या करवाना है")
    c.add_argument("--tukde", nargs="*", help="ख़ुद बाँटकर देना हो तो")
    c.add_argument("--chakkar", type=int, help="अधिकतम चक्कर")

    up.add_parser("hisaab", help="पिछली सभाओं का हिसाब")
    up.add_parser("nakli", help="नक़ली सभा चलाकर देखो")
    up.add_parser("darpan", help="खिड़की खोलो (tkinter)")

    a = p.parse_args()

    if a.hukum == "jaancho":
        return hukum_jaancho()
    if a.hukum == "chalao":
        return hukum_chalao(a.kaam, a.tukde, a.chakkar)
    if a.hukum == "hisaab":
        return hukum_hisaab()
    if a.hukum == "nakli":
        return hukum_nakli()
    if a.hukum == "darpan":
        return hukum_darpan()

    p.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(mukhya())
    except KeyboardInterrupt:
        print("\n\n  रोक दिया गया. जो हुआ वो बही-खाते में दर्ज है.\n")
        sys.exit(130)
