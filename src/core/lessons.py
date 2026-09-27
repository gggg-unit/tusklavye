"""Progressive 10-finger typing curriculum (Turkish content).

Lessons go from home row basics to full keyboard mastery, each with a
description, the keys introduced, and practice text.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any

LESSONS: List[Dict[str, Any]] = [
    {
        "id": "L01",
        "title": "Ana Satır - Sol El",
        "description": "Sol el ana satır tuşlarını öğren: a s d f",
        "keys": ["a", "s", "d", "f"],
        "text": "asdf asdf asdf asdf asdf\nsadf sadf sadf sadf sadf\ndafs dafs dafs dafs dafs\nfasd fasd fasd fasd fasd",
        "target_wpm": 15,
    },
    {
        "id": "L02",
        "title": "Ana Satır - Sağ El",
        "description": "Sağ el ana satır tuşlarını öğren: j k l ş",
        "keys": ["j", "k", "l", "ş"],
        "text": "jklş jklş jklş jklş jklş\nklşj klşj klşj klşj klşj\nlşjk lşjk lşjk lşjk lşjk\nşjkl şjkl şjkl şjkl şjkl",
        "target_wpm": 15,
    },
    {
        "id": "L03",
        "title": "Ana Satır - Tamamı",
        "description": "İki el birlikte ana satır: a s d f j k l ş",
        "keys": ["a", "s", "d", "f", "j", "k", "l", "ş"],
        "text": "asdf jklş asdf jklş asdf jklş\ndaks jşlk daks jşlk daks jşlk\nfjdk slşa fjdk slşa fjdk slşa\nalkış dakika falaka şakada",
        "target_wpm": 20,
    },
    {
        "id": "L04",
        "title": "Üst Satır - Sol El",
        "description": "Sol el üst satır: q w e r t",
        "keys": ["q", "w", "e", "r", "t"],
        "text": "qwert qwert qwert qwert\nwertq wertq wertq wertq\ntrewq trewq trewq trewq\nerwtq erwtq erwtq erwtq",
        "target_wpm": 18,
    },
    {
        "id": "L05",
        "title": "Üst Satır - Sağ El",
        "description": "Sağ el üst satır: y u ı o p",
        "keys": ["y", "u", "ı", "o", "p"],
        "text": "yuıop yuıop yuıop yuıop\nıopyu ıopyu ıopyu ıopyu\npouyı pouyı pouyı pouyı\nuıypo uıypo uıypo uıypo",
        "target_wpm": 18,
    },
    {
        "id": "L06",
        "title": "Üst Satır - Tamamı",
        "description": "Tüm üst satır: q w e r t y u ı o p",
        "keys": ["q", "w", "e", "r", "t", "y", "u", "ı", "o", "p"],
        "text": "qwertyuıop qwertyuıop qwertyuıop\nportakal teyp ırak puro wet\nyaprak pırtık ortalama türk\npencere yorgun ırmak tereyağı",
        "target_wpm": 22,
    },
    {
        "id": "L07",
        "title": "Alt Satır - Sol El",
        "description": "Sol el alt satır: z x c v b",
        "keys": ["z", "x", "c", "v", "b"],
        "text": "zxcvb zxcvb zxcvb zxcvb\ncvbxz cvbxz cvbxz cvbxz\nbvcxz bvcxz bvcxz bvcxz\nxzc vb xzc vb xzc vb",
        "target_wpm": 18,
    },
    {
        "id": "L08",
        "title": "Alt Satır - Sağ El",
        "description": "Sağ el alt satır: n m ö ç .",
        "keys": ["n", "m", "ö", "ç", "."],
        "text": "nmöç. nmöç. nmöç. nmöç.\nöçmn. öçmn. öçmn. öçmn.\nmn.çö mn.çö mn.çö mn.çö\nçöm.n çöm.n çöm.n çöm.n",
        "target_wpm": 18,
    },
    {
        "id": "L09",
        "title": "Türkçe Karakterler",
        "description": "Türkçe'ye özel tuşlar: ğ ü i ş ö ç",
        "keys": ["ğ", "ü", "i", "ş", "ö", "ç"],
        "text": "ğüşöçi ğüşöçi ğüşöçi ğüşöçi\nşişçe şişçe şişçe şişçe\ngöğüç göğüç göğüç göğüç\nöğretmen çiçek ağaç düğün",
        "target_wpm": 20,
    },
    {
        "id": "L10",
        "title": "Sayılar ve Noktalama",
        "description": "Rakamlar ve işaretler: 1 2 3 4 5 6 7 8 9 0",
        "keys": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        "text": "12345 67890 12345 67890\n54321 09876 54321 09876\n192837 465019 283746\n05 10 15 20 25 30 35 40 45 50",
        "target_wpm": 20,
    },
    {
        "id": "L11",
        "title": "Kelime Pratiği",
        "description": "Yaygın Türkçe kelimelerle hız pratiği",
        "keys": [],
        "text": "merhaba dünya ve türkiye\nbilgisayar klavye parmak yazma\nher gün düzenli pratik yap\nhız ve doğruluk zamanla gelir",
        "target_wpm": 25,
    },
    {
        "id": "L12",
        "title": "Cümle Pratiği",
        "description": "Tam cümlelerle akış pratiği",
        "keys": [],
        "text": "On parmak yazma, her tuşa doğru parmakla basmayı gerektirir.\nDüzenli pratik ile yazma hızı ve doğruluk giderek artar.\nKlavyeye bakmadan yazmak, gözün ekranda kalmasını sağlar.\nTürkçe klavyede Türkçe karakterler kolayca yazılabilir.",
        "target_wpm": 30,
    },
    {
        "id": "L13",
        "title": "Paragraf Pratiği",
        "description": "Uzun paragraflarla dayanıklılık pratiği",
        "keys": [],
        "text": (
            "On parmak yazma yöntemi, her bir parmağın klavye üzerinde belirli bir bölgeye atanmasıyla çalışır. "
            "Bu sayede yazarken klavyeye bakmaya gerek kalmaz ve yazma hızı önemli ölçüde artar. "
            "Başlangıçta yavaş hissedilir ancak sabırlı ve düzenli pratik yaparak büyük ilerleme kaydedilir.\n"
            "Doğru parmak kullanımı, hataları azaltır ve yazarken yorulmayı önler. "
            "Her gün on beş dakika bile pratik yapmak, uzun vadede büyük fark yaratır."
        ),
        "target_wpm": 35,
    },
    {
        "id": "L14",
        "title": "İleri Düzey",
        "description": "Karmaşık metinlerle ustalık seviyesi",
        "keys": [],
        "text": (
            "Teknoloji, günümüzde hayatın her alanına derinlemesine nüfuz etmiştir. "
            "Bilgisayarlar, akıllı telefonlar ve internet, iletişimi ve bilgiye erişimi kökten değiştirmiştir. "
            "Hızlı ve doğru yazma becerisi, bu dijital dünyada verimli olmanın temel anahtarlarından biridir.\n"
            "On parmak yazma tekniğini öğrenen bir kişi, hem zamandan tasarruf eder hem de daha az yorgunluk hisseder. "
            "Klavyeyi doğru kullanmak, profesyonel ve akademik yaşamda büyük bir avantaj sağlar."
        ),
        "target_wpm": 40,
    },
    {
        "id": "L15",
        "title": "İstiklal Marşı - 1. ve 2. Kıta",
        "description": "Millî marşımızın ilk iki kıtasını yaz",
        "keys": [],
        "text": (
            "Korkma! Sönmez bu şafaklarda yüzen al sancak,\n"
            "Sönmeden yurdumun üstünde tüten en son ocak.\n"
            "O benim milletimin yıldızıdır, parlayacak;\n"
            "O benimdir, o benim milletimindir ancak.\n"
            "Çatma, kurban olayım, çehreni ey nazlı hilal!\n"
            "Kahraman ırkıma bir gül; ne bu şiddet, bu celal?\n"
            "Sana olmaz dökülen kanlarımız sonra helal...\n"
            "Hakkıdır, Hakk'a tapan milletimin istiklal!"
        ),
        "target_wpm": 35,
    },
]


def get_lesson(lesson_id: str) -> Optional[dict]:
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_lesson_index(lesson_id: str) -> int:
    for i, lesson in enumerate(LESSONS):
        if lesson["id"] == lesson_id:
            return i
    return -1