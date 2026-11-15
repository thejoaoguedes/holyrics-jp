#!/usr/bin/env python3
"""Gera a Bíblia japonesa JA1955 (口語訳 / Kougo-yaku) em romaji.

Lê o texto OSIS de domínio público (com a leitura de cada kanji anotada em
furigana) e grava, em dist/, a mesma Bíblia transliterada para o alfabeto
latino em vários formatos de módulo bíblico, para importar no Holyrics.

Uso:
    pip install -r requirements.txt
    python build.py
"""
import gzip
import html
import json
import re
import sqlite3
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import cutlet

ROOT = Path(__file__).parent
SOURCE = ROOT / "source" / "jpn-kougo.osis.xml.gz"
VERSIFICATION = ROOT / "source" / "kjv_versification.json"
DIST = ROOT / "dist"

ABBR = "JA1955-ROMAJI"
TITLE = "Kougo-yaku 1955 (Romaji)"
DESCRIPTION = (
    "Japanese Colloquial Bible 1954/1955 (口語訳, public domain), "
    "romanized (Hepburn) from the furigana readings."
)

# (id OSIS, nome em inglês, abreviação, número do livro no MyBible)
BOOKS = [
    ("Gen", "Genesis", "Gen", 10), ("Exod", "Exodus", "Exo", 20),
    ("Lev", "Leviticus", "Lev", 30), ("Num", "Numbers", "Num", 40),
    ("Deut", "Deuteronomy", "Deu", 50), ("Josh", "Joshua", "Jos", 60),
    ("Judg", "Judges", "Jdg", 70), ("Ruth", "Ruth", "Rut", 80),
    ("1Sam", "1 Samuel", "1Sa", 90), ("2Sam", "2 Samuel", "2Sa", 100),
    ("1Kgs", "1 Kings", "1Ki", 110), ("2Kgs", "2 Kings", "2Ki", 120),
    ("1Chr", "1 Chronicles", "1Ch", 130), ("2Chr", "2 Chronicles", "2Ch", 140),
    ("Ezra", "Ezra", "Ezr", 150), ("Neh", "Nehemiah", "Neh", 160),
    ("Esth", "Esther", "Est", 190), ("Job", "Job", "Job", 220),
    ("Ps", "Psalms", "Psa", 230), ("Prov", "Proverbs", "Pro", 240),
    ("Eccl", "Ecclesiastes", "Ecc", 250), ("Song", "Song of Solomon", "Sng", 260),
    ("Isa", "Isaiah", "Isa", 290), ("Jer", "Jeremiah", "Jer", 300),
    ("Lam", "Lamentations", "Lam", 310), ("Ezek", "Ezekiel", "Ezk", 330),
    ("Dan", "Daniel", "Dan", 340), ("Hos", "Hosea", "Hos", 350),
    ("Joel", "Joel", "Jol", 360), ("Amos", "Amos", "Amo", 370),
    ("Obad", "Obadiah", "Oba", 380), ("Jonah", "Jonah", "Jon", 390),
    ("Mic", "Micah", "Mic", 400), ("Nah", "Nahum", "Nam", 410),
    ("Hab", "Habakkuk", "Hab", 420), ("Zeph", "Zephaniah", "Zep", 430),
    ("Hag", "Haggai", "Hag", 440), ("Zech", "Zechariah", "Zec", 450),
    ("Mal", "Malachi", "Mal", 460), ("Matt", "Matthew", "Mat", 470),
    ("Mark", "Mark", "Mrk", 480), ("Luke", "Luke", "Luk", 490),
    ("John", "John", "Jhn", 500), ("Acts", "Acts", "Act", 510),
    ("Rom", "Romans", "Rom", 520), ("1Cor", "1 Corinthians", "1Co", 530),
    ("2Cor", "2 Corinthians", "2Co", 540), ("Gal", "Galatians", "Gal", 550),
    ("Eph", "Ephesians", "Eph", 560), ("Phil", "Philippians", "Php", 570),
    ("Col", "Colossians", "Col", 580), ("1Thess", "1 Thessalonians", "1Th", 590),
    ("2Thess", "2 Thessalonians", "2Th", 600), ("1Tim", "1 Timothy", "1Ti", 610),
    ("2Tim", "2 Timothy", "2Ti", 620), ("Titus", "Titus", "Tit", 630),
    ("Phlm", "Philemon", "Phm", 640), ("Heb", "Hebrews", "Heb", 650),
    ("Jas", "James", "Jas", 660), ("1Pet", "1 Peter", "1Pe", 670),
    ("2Pet", "2 Peter", "2Pe", 680), ("1John", "1 John", "1Jn", 690),
    ("2John", "2 John", "2Jn", 700), ("3John", "3 John", "3Jn", 710),
    ("Jude", "Jude", "Jud", 720), ("Rev", "Revelation", "Rev", 730),
]
BOOK_INDEX = {b[0]: i for i, b in enumerate(BOOKS)}


# ---------------------------------------------------------------- leitura OSIS

TAG = re.compile(r"<[^>]+>")
VERSE_OPEN = re.compile(r'<verse\b[^>]*\bosisID="([^"]+)"[^>]*?(/?)>')
W_OPEN = re.compile(r'<w\b[^>]*\bgloss="([^"]*)"')


def parse_osis(path):
    """Devolve {(livro, capítulo, versículo): [(texto, leitura ou None), ...]}
    e o prefixo "[9-10] " dos versículos que a fonte traz juntos."""
    xml = gzip.open(path, "rt", encoding="utf-8").read()
    verses, joined = {}, {}
    current = None  # lista de segmentos do versículo aberto
    gloss = None  # leitura do <w> aberto
    skip = 0  # dentro de <title>
    pos = 0
    for m in TAG.finditer(xml):
        text = xml[pos:m.start()]
        pos = m.end()
        if text and current is not None and not skip:
            text = re.sub(r"\s+", "", html.unescape(text))
            if text:
                current.append((text, gloss))
        tag = m.group(0)
        if tag.startswith("<title"):
            skip += 1
        elif tag.startswith("</title"):
            skip -= 1
        elif tag.startswith("<w"):
            g = W_OPEN.match(tag)
            gloss = g.group(1) if g else None
        elif tag.startswith("</w"):
            gloss = None
        elif tag.startswith("<verse"):
            v = VERSE_OPEN.match(tag)
            if v:
                # A fonte junta alguns versículos ("Rom.1.9 Rom.1.10"): o
                # mesmo texto vale para todos, marcado com o intervalo.
                keys = []
                for osis_id in v.group(1).split():
                    book, chapter, verse = osis_id.split("!")[0].split(".")
                    keys.append((BOOK_INDEX[book], int(chapter), int(verse)))
                current = verses.setdefault(keys[0], [])
                for key in keys[1:]:
                    verses[key] = current
                if len(keys) > 1:
                    joined.update(dict.fromkeys(
                        keys, f"[{keys[0][2]}-{keys[-1][2]}] "))
            else:  # <verse eID="..."/>
                current = None
        elif tag.startswith("</verse"):
            current = None
    return verses, joined


# -------------------------------------------------------------- romanização

KANJI = re.compile(r"[㐀-鿿々〆]")
KATAKANA_WORD = re.compile(r"[ァ-ヺー]+")


# substantivos comuns escritos em katakana (não levam maiúscula)
COMMON_KATAKANA = set(
    "パン キュビト シケル ラッパ バプテスマ タラント オリブ エパ ヒン ホメル "
    "ミナ デナリ ゲラ ベカ コル バテ エポデ ケルビム ケルブ セラピム アァメン "
    "アーメン ハレルヤ マナ ホサナ ラビ ウリム トンミム レビヤタン セラ "
    "ガラス ランプ ミルラ メートル マイル アカシヤ レプタ コドラント "
    "アサリオン スタデオン ペスト テラピム パウンド ヒソプ".split())


class _NoTitle(str):
    def title(self):
        return self


class Romanizer(cutlet.Cutlet):
    """Cutlet, mas usando a leitura do furigana em vez da do dicionário."""

    def __init__(self):
        super().__init__(use_foreign_spelling=False)
        self.use_wo = False  # partícula を -> "o", como se pronuncia
        self.readings = {}
        self.table["・"] = " "
        # marcadores trocados por aspas em tidy(), que precisa saber qual
        # abre e qual fecha (uma fala pode começar num versículo e terminar
        # em outro)
        self.table.update({"「": "\x01", "」": "\x02", "『": "\x03", "』": "\x04"})
        self.table["―"] = " - "
        self.table["〔"] = "["
        self.table["〕"] = "]"
        self.table["…"] = "..."

    def romaji_word(self, word):
        if word.surface == "主に":  # o dicionário lê como "omo ni" (principalmente)
            return _NoTitle("Shu ni")
        reading = self.readings.get(id(word))
        if reading is None:
            roma = super().romaji_word(word)
        else:
            roma = self.map_kana(reading)
        # Maiúscula só em "Shu" (主) e nos nomes em katakana; o dicionário
        # marca substantivos comuns como nome próprio com frequência.
        if word.surface == "主" or (KATAKANA_WORD.fullmatch(word.surface)
                                   and word.surface not in COMMON_KATAKANA):
            roma = roma[:1].upper() + roma[1:]
        return _NoTitle(roma)

    def verse(self, segments):
        text = "".join(t for t, _ in segments)
        words = list(self.tagger(text))
        if "".join(w.surface for w in words) != text:
            raise ValueError("tokenização não bate com o texto: " + text)

        # Posição de cada segmento com furigana dentro do texto.
        ruby, offset = [], 0
        for t, reading in segments:
            if reading is not None:
                ruby.append((offset, offset + len(t), reading))
            offset += len(t)

        # A leitura de cada palavra é o kana do próprio texto, trocando cada
        # trecho com furigana pela leitura anotada. Um trecho que atravessa
        # duas palavras fica inteiro na primeira.
        self.readings = {}
        offset, ri = 0, 0
        for w in words:
            start, end = offset, offset + len(w.surface)
            offset = end
            if not KANJI.search(w.surface) and not (
                    ri < len(ruby) and ruby[ri][0] < end):
                continue
            reading, cursor = "", start
            while ri < len(ruby) and ruby[ri][0] < end:
                rs, re_, rr = ruby[ri]
                if rs >= cursor:
                    reading += text[cursor:rs] + rr
                cursor = max(cursor, min(re_, end))
                if re_ > end:  # o trecho continua na palavra seguinte
                    ruby[ri] = (end, re_, "")
                    break
                ri += 1
            reading += text[cursor:end]
            if not KANJI.search(reading):
                self.readings[id(w)] = reading

        tokens = self.romaji_tokens(words, capitalize=True)
        # Nomes bíblicos que o dicionário não conhece saem em pedaços
        # ("Ira De"): pedaços de katakana vizinhos são uma palavra só.
        for i in range(1, len(words)):
            if (KATAKANA_WORD.fullmatch(words[i].surface)
                    and KATAKANA_WORD.fullmatch(words[i - 1].surface)):
                tokens[i - 1].space = False
                tokens[i].surface = tokens[i].surface.lower()
        return tidy("".join(str(t) for t in tokens))


def tidy(s):
    s = s.replace("{", "")
    s = re.sub(r"\s*\x01\s*", ' \x01', s)  # abre: espaço só antes
    s = re.sub(r"\s*\x03\s*", ' \x03', s)
    s = re.sub(r"\s*\x02", '\x02 ', s)  # fecha: espaço só depois
    s = re.sub(r"\s*\x04", '\x04 ', s)
    # maiúscula ao abrir aspas
    s = re.sub(r"([\x01\x03])([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    s = s.translate({1: '"', 2: '"', 3: "'", 4: "'"})
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,.;:!?\]])", r"\1", s)
    s = re.sub(r"([\[(])\s+", r"\1", s)
    # prefixo honorífico み escrito em kana ("のみ名") gruda no "no" anterior
    s = re.sub(r"\bnomi (mae|na|waza|kokoro|te|moto|kotoba|koe|kao|mune|tsukai|"
               r"tsuge|sumai|kura|chikara|za|ude)\b", r"no mi\1", s)
    if s.count("[") > s.count("]"):  # "[Sera" vem sem fechar na fonte
        s += "]"
    # maiúscula no início de cada frase
    s = re.sub(r"""(^|[.!?]["'\]]? +)([a-z])""",
               lambda m: m.group(1) + m.group(2).upper(), s)
    return s


# ------------------------------------------------------------------ formatos

def write_txt(rows, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for b, c, v, text in rows:
            f.write(f"{BOOKS[b][1]} {c}:{v}\t{text}\n")


def write_json(rows, path):
    books = []
    for b, c, v, text in rows:
        if len(books) <= b:
            books.append({"name": BOOKS[b][1], "abbr": BOOKS[b][2], "chapters": []})
        chapters = books[b]["chapters"]
        if len(chapters) < c:
            chapters.append([])
        chapters[c - 1].append(text)
    data = {"abbreviation": ABBR, "title": TITLE, "language": "ja",
            "description": DESCRIPTION, "books": books}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def write_theword(rows, path):
    # Uma linha por versículo, na ordem e na contagem da KJV.
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        for _, _, _, text in rows:
            f.write(text + "\n")
        f.write("\n")
        f.write(f"short.title={ABBR}\n")
        f.write(f"description={TITLE}\n")
        f.write("lang=ja\n")
        f.write(f"about={DESCRIPTION}\n")


def _sqlite(path):
    path.unlink(missing_ok=True)
    return sqlite3.connect(path)


def write_mysword(rows, path, esword=False):
    # MySword (.bbl.mybible) e e-Sword (.bblx) usam o mesmo esquema.
    db = _sqlite(path)
    db.execute(
        "CREATE TABLE Details (Description NVARCHAR(255), Abbreviation NVARCHAR(50),"
        " Comments TEXT, Version TEXT, VersionDate DATETIME, PublishDate DATETIME,"
        " RightToLeft BOOL, OT BOOL, NT BOOL, Strong BOOL"
        + ("" if esword else ", Language TEXT") + ")")
    details = [TITLE, ABBR, DESCRIPTION, "1.0", "2026-11-15", "1955-01-01", 0, 1, 1, 0]
    if not esword:
        details.append("jpn")
    db.execute(f"INSERT INTO Details VALUES ({','.join('?' * len(details))})", details)
    db.execute("CREATE TABLE Bible (Book INT, Chapter INT, Verse INT, Scripture TEXT)")
    db.executemany("INSERT INTO Bible VALUES (?,?,?,?)",
                   [(b + 1, c, v, text) for b, c, v, text in rows])
    db.execute("CREATE UNIQUE INDEX bible_key ON Bible (Book ASC, Chapter ASC, Verse ASC)")
    db.commit()
    db.execute("VACUUM")
    db.close()


def write_mybible(rows, path):
    db = _sqlite(path)
    db.execute("CREATE TABLE info (name TEXT, value TEXT)")
    db.executemany("INSERT INTO info VALUES (?,?)", [
        ("description", TITLE), ("detailed_info", DESCRIPTION),
        ("language", "ja"), ("chapter_string", "Chapter"),
        ("russian_numbering", "false"), ("strong_numbers", "false"),
        ("right_to_left", "false"),
    ])
    db.execute("CREATE TABLE books (book_color TEXT, book_number NUMERIC,"
               " short_name TEXT, long_name TEXT)")
    db.executemany("INSERT INTO books VALUES (?,?,?,?)",
                   [("#ccccff", num, abbr, name) for _, name, abbr, num in BOOKS])
    db.execute("CREATE TABLE verses (book_number NUMERIC, chapter NUMERIC,"
               " verse NUMERIC, text TEXT)")
    db.executemany("INSERT INTO verses VALUES (?,?,?,?)",
                   [(BOOKS[b][3], c, v, text) for b, c, v, text in rows])
    db.execute("CREATE UNIQUE INDEX verses_index ON verses (book_number, chapter, verse)")
    db.commit()
    db.execute("VACUUM")
    db.close()


def _write_xml(rows, path, head, tail, book, chapter, verse, book_end, chapter_end):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + head)
        last = (None, None)
        for b, c, v, text in rows:
            if b != last[0]:
                if last[0] is not None:
                    f.write(chapter_end + book_end)
                f.write(book(b))
                last = (b, None)
            if c != last[1]:
                if last[1] is not None:
                    f.write(chapter_end)
                f.write(chapter(c))
                last = (b, c)
            f.write(verse(v, escape(text)))
        f.write(chapter_end + book_end + tail)


def write_zefania(rows, path):
    _write_xml(
        rows, path,
        head=(f"<XMLBIBLE biblename={quoteattr(TITLE)} type=\"x-bible\">\n"
              f"<INFORMATION><title>{escape(TITLE)}</title>"
              f"<identifier>{ABBR}</identifier>"
              f"<description>{escape(DESCRIPTION)}</description>"
              "<language>JPN</language><rights>Public Domain</rights>"
              "</INFORMATION>\n"),
        tail="</XMLBIBLE>\n",
        book=lambda b: (f'<BIBLEBOOK bnumber="{b + 1}" bname={quoteattr(BOOKS[b][1])}'
                        f' bsname={quoteattr(BOOKS[b][2])}>\n'),
        chapter=lambda c: f'<CHAPTER cnumber="{c}">\n',
        verse=lambda v, t: f'<VERS vnumber="{v}">{t}</VERS>\n',
        book_end="</BIBLEBOOK>\n", chapter_end="</CHAPTER>\n")


def write_opensong(rows, path):
    _write_xml(
        rows, path, head="<bible>\n", tail="</bible>\n",
        book=lambda b: f"<b n={quoteattr(BOOKS[b][1])}>\n",
        chapter=lambda c: f'<c n="{c}">\n',
        verse=lambda v, t: f'<v n="{v}">{t}</v>\n',
        book_end="</b>\n", chapter_end="</c>\n")


# ---------------------------------------------------------------------- main

def main():
    source, joined = parse_osis(SOURCE)
    counts = json.loads(VERSIFICATION.read_text())
    romanizer = Romanizer()

    rows, missing = [], []
    for b, chapters in enumerate(counts):
        for c, n in enumerate(chapters, 1):
            for v in range(1, n + 1):
                segments = source.pop((b, c, v), None)
                if not segments:
                    missing.append(f"{BOOKS[b][1]} {c}:{v}")
                    rows.append((b, c, v, ""))
                    continue
                rows.append((b, c, v, joined.get((b, c, v), "")
                             + romanizer.verse(segments)))
        print(f"\r{b + 1}/66 {BOOKS[b][1]:<20}", end="", file=sys.stderr)
    print(file=sys.stderr)

    # A numeração japonesa tem três versículos a mais que a da KJV
    # (Sl 47:10, 3Jo 15, Ap 12:18): entram no fim do versículo anterior.
    index = {(b, c, v): i for i, (b, c, v, _) in enumerate(rows)}
    for (b, c, v) in sorted(source):
        if (b, c, v - 1) in index and v == counts[b][c - 1] + 1:
            i = index[(b, c, v - 1)]
            extra = romanizer.verse(source.pop((b, c, v)))
            rows[i] = (b, c, v - 1, f"{rows[i][3]} [{v}] {extra}")

    if source:
        sys.exit(f"versículos fora da numeração esperada: {sorted(source)[:10]}")
    bad = [f"{BOOKS[b][1]} {c}:{v}: {t}" for b, c, v, t in rows
           if re.search(r"[^\x20-\x7e]|\?\?", t)]
    if bad:
        sys.exit("romanização incompleta:\n" + "\n".join(bad[:20]))

    DIST.mkdir(exist_ok=True)
    for old in DIST.iterdir():
        old.unlink()
    write_txt(rows, DIST / f"{ABBR}.txt")
    write_json(rows, DIST / f"{ABBR}.json")
    write_theword(rows, DIST / f"{ABBR}.ont")
    write_mysword(rows, DIST / f"{ABBR}.bbl.mybible")
    write_mysword(rows, DIST / f"{ABBR}.bblx", esword=True)
    write_mybible(rows, DIST / f"{ABBR}.SQLite3")
    write_zefania(rows, DIST / f"{ABBR}.zefania.xml")
    write_opensong(rows, DIST / f"{ABBR}.opensong.xml")

    print(f"{len(rows)} versículos, {len(missing)} sem texto na fonte"
          + (f": {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
