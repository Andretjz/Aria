"""Shared constants ported from Transcribit v6.

All word lists, patterns, and tuning constants live here so every module
reads from one source of truth. Never import module-level symbols from
aria.modules.* — use this file instead.
"""
from __future__ import annotations

# ── Stop words (5 target languages) ────────────────────────────────────────
# Used by vocabulary extraction to filter out function words before ranking.
STOP_WORDS: set[str] = {
    # German
    "ich","du","er","sie","es","wir","ihr","und","oder","aber","denn","weil",
    "dass","die","der","das","ein","eine","einen","einem","einer","eines",
    "ist","bin","bist","sind","war","hatte","haben","hat","wird","wurde",
    "werden","kann","muss","soll","will","darf","mag","möchte","in","an",
    "auf","bei","mit","nach","von","vor","zu","zum","zur","aus","durch",
    "für","über","unter","zwischen","gegen","ohne","um","als","wie","auch",
    "noch","schon","immer","nie","nicht","kein","keine","ja","nein","ok",
    "so","dann","mal","doch","halt","sehr","ganz","einfach","nur","hier",
    "da","dort","wenn","wann","wo","was","wer","warum","welche","mein",
    "meine","dein","sein","ihre","unser","mir","mich","dir","sich","uns",
    "euch","ihnen","ihm","ihn","genau","gut","super","gerne","natürlich",
    "eigentlich","irgendwie","jetzt","schon","habe","haben","hatte",
    "diesem","dieser","diese","dieses","viel","viele","mehr","beim","vom",
    # English
    "i","you","he","the","a","an","is","are","was","were","be","have","has",
    "do","does","did","will","would","could","should","to","of","in","on",
    "at","by","for","with","that","this","my","your","his","her","its",
    "our","me","him","us","them","what","which","who","not","no","yes",
    "just","very","also","well","now","then","here","there","all","more",
    # Spanish
    "yo","tú","él","ella","nosotros","ellos","y","o","pero","que","es",
    "un","una","los","las","del","al",
    # French
    "je","tu","il","nous","vous","ils","et","ou","mais","que","est",
    "un","une","le","la","les",
    # Italian
    "io","tu","lui","noi","voi","loro","e","o","ma","che","è","un","una","il","la",
}

# ── Name blocklist ──────────────────────────────────────────────────────────
# Tokens that regex name patterns might extract but are never real names.
NAME_BLOCKLIST: set[str] = {
    "psychologin","trainerin","trainer","leiterin","leiter","entwicklerin",
    "entwickler","managerin","manager","direktin","direktor","digital",
    "learning","developerin","developer","teamleiterin","teamleiter",
    "bildung","neuropsychologie","kommunikation","ich","du","er","sie",
    "wir","das","ein","eine","der","die","hier","gut","sehr","auch","mal",
    "ja","nein","ok","heute","jetzt","dann","aber","doch","gerne","genau",
    "frau","herr","i","you","he","she","we","the","a","an","this","here",
    "good","yes","no","right","well","just","now","today","sure",
    "froh","glücklich","traurig","müde","nervös","gespannt","bereit",
    "fertig","sicher","klar","wichtig","richtig","falsch","dankbar",
    "erfreut","zufrieden","begeistert","überrascht","stolz","neugierig",
    "leider","insofern","natürlich","eigentlich","tatsächlich",
}

# ── Name resolution patterns (per language) ─────────────────────────────────
# Each language has "self" patterns (speaker introduces themselves) and
# "other" patterns (speaker addresses someone by name).
NAME_PATTERNS: dict[str, dict[str, list[tuple[str, int]]]] = {
    "de": {
        "self":  [
            (r"\bich bin (\w+)\b", 1),
            (r"\bich hei[sß]e (\w+)\b", 1),
            (r"\bmein name ist (\w+)\b", 1),
        ],
        "other": [
            (r"\bhallo[,]? (\w+)\b", 1),
            (r"\bwillkommen[,]? (\w+)\b", 1),
            (r"\bdas ist (\w+)\b", 1),
            (r"\b(\w+)[,] stell\b", 1),
            (r"\bentschuldigung[,]? (\w+)\b", 1),
        ],
    },
    "en": {
        "self":  [
            (r"\bi am (\w+)\b", 1),
            (r"\bmy name is (\w+)\b", 1),
            (r"\bi['']m (\w+)\b", 1),
        ],
        "other": [
            (r"\bwelcome[,]? (\w+)\b", 1),
            (r"\bthis is (\w+)\b", 1),
            (r"\bhere(?:'s| is) (\w+)\b", 1),
        ],
    },
    "es": {
        "self":  [
            (r"\bme llamo (\w+)\b", 1),
            (r"\bsoy (\w+)\b", 1),
            (r"\bmi nombre es (\w+)\b", 1),
        ],
        "other": [
            (r"\bbienvenido[,]? (\w+)\b", 1),
            (r"\beste es (\w+)\b", 1),
        ],
    },
    "fr": {
        "self":  [
            (r"\bje m'appelle (\w+)\b", 1),
            (r"\bje suis (\w+)\b", 1),
        ],
        "other": [
            (r"\bbienvenue[,]? (\w+)\b", 1),
            (r"\bc'est (\w+)\b", 1),
        ],
    },
    "it": {
        "self":  [
            (r"\bmi chiamo (\w+)\b", 1),
            (r"\bsono (\w+)\b", 1),
        ],
        "other": [
            (r"\bbenvenuto[,]? (\w+)\b", 1),
            (r"\bquesto è (\w+)\b", 1),
        ],
    },
}

# ── Denglisch — English words commonly embedded in German speech ────────────
# Used by pass5_blueprints.py to detect code-switching.
ENGLISH_IN_GERMAN: set[str] = {
    "meeting","meetings","call","calls","update","updates","feedback",
    "team","teams","okay","ok","sorry","anyway","actually","basically",
    "workshop","workshops","onboarding","offboarding","deadline","deadlines",
    "follow","followup","follow-up","check","checkin","checkout","pipeline",
    "remote","homeoffice","freelance","startup","pitch","pitching","content",
    "skills","skill","performance","review","reviews","project","projects",
    "manager","management","lead","leadership","coaching","coach","training",
    "mindset","community","impact","output","input","outcome","outcomes",
    "challenge","challenges","highlight","highlights","learnings","learning",
    "roadmap","rollout","setup","workflow","workflows","dashboard","report",
    "reports","sprint","sprints","release","releases","feature","features",
    "bug","bugs","fix","fixes","testing","test","deployment","deployment",
    "digital","online","offline","live","stream","streaming","broadcast",
    "rebranding","branding","marketing","campaign","campaigns","target",
    "networking","network","platform","platforms","app","apps","tool",
    "tools","data","analytics","insights","benchmark","kpi","kpis",
    "e-learning","elearning","webinar","webinars","podcast","podcasts",
    "storytelling","brainstroming","brainstorming","ideation","prototype",
    "prototyping","agile","scrum","kanban","backlog","stakeholder",
}

# ── Supported target languages ──────────────────────────────────────────────
TARGET_LANGUAGES: dict[str, str] = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
}

# ── CEFR levels for vocabulary ranking ─────────────────────────────────────
CEFR_LEVELS: list[str] = ["A1", "A2", "B1", "B2", "C1", "C2"]

# ── Audio pipeline constants ────────────────────────────────────────────────
SAMPLE_RATE: int = 16_000
COLD_START_S: int = 60
COLD_THRESH: float = 0.45
MIN_SEG_SAMPLES: int = 8_000
MIN_EMBED_DUR: float = 1.5
NAME_CONF_THRES: int = 2
EMBED_THRESH: float = 0.50
