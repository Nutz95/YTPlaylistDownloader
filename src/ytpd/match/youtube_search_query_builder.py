import re
import unicodedata

_FEAT_PATTERN = re.compile(
    r"\s*[\(\[]?\s*(?:feat\.?|ft\.?|featuring)\b[^\)\]]*[\)\]]?",
    re.IGNORECASE,
)
_PAREN_OR_BRACKET = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_MULTI_SPACE = re.compile(r"\s+")
_COLON_SPLIT = re.compile(r"\s+:\s+")
_QUOTED_DOUBLE = re.compile(r'"([^"]{4,120})"')
_QUOTED_GUILLEMETS = re.compile(r"«([^»]{4,120})»")
_ACT_ARIA = re.compile(
    r"(?:act\s*\d+|acte\s*\d+).{0,40}?([A-Za-zÀ-ÿ][^\[\]]{8,80})",
    re.IGNORECASE,
)


class YoutubeSearchQueryBuilder:
    """Build primary and fallback YouTube search strings for one track."""

    def primary(self, artist: str, title: str) -> str:
        """Return the preferred search query (feat tags and colon spam stripped)."""
        return self._join(artist, self._clean_title(title))

    def fallbacks(self, artist: str, title: str) -> list[str]:
        """Return alternate queries when the primary search returns no hits."""
        cleaned_title = self._clean_title(title)
        folded_artist = self._fold_accents(artist.strip())
        folded_title = self._fold_accents(cleaned_title)
        quoted = self._quoted_phrase(title)
        aria = self._aria_hint(title)
        candidates = [
            self._join(folded_artist, folded_title),
            self._join(artist, self._first_colon_segment(cleaned_title)),
            self._join(folded_artist, folded_title, "lyrics"),
            self._join(folded_artist, folded_title, "audio"),
            self._join(folded_title, "generique"),
            self._join(folded_title, "theme"),
            self._join(quoted, "generique") if quoted else "",
            self._join(aria, "verdi") if aria else "",
            self._join(aria) if aria else "",
            self._join(folded_title, "soundtrack"),
        ]
        return self._unique_excluding_primary(artist, title, candidates)

    def retry_queries(self, artist: str, title: str) -> list[str]:
        """Return extra queries for a second match pass after an LLM rejection."""
        cleaned_title = self._clean_title(title)
        folded_artist = self._fold_accents(artist.strip())
        folded_title = self._fold_accents(cleaned_title)
        quoted = self._quoted_phrase(title)
        aria = self._aria_hint(title)
        candidates = [
            self._join(folded_artist, folded_title, "official audio"),
            self._join(folded_artist, folded_title, "topic"),
            self._join(artist, cleaned_title, "official"),
            self._join(folded_title, folded_artist),
            self._join(quoted, "full") if quoted else "",
            self._join(aria, "traviata") if aria else "",
            self._join(folded_title, "chorus"),
            self._join(folded_title, "anime"),
        ]
        return self._unique_excluding_primary(artist, title, candidates)

    def _unique_excluding_primary(
        self,
        artist: str,
        title: str,
        candidates: list[str],
    ) -> list[str]:
        primary = self.primary(artist, title)
        unique: list[str] = []
        seen: set[str] = {primary}
        for query in candidates:
            if query == "" or query in seen:
                continue
            seen.add(query)
            unique.append(query)
        return unique

    def _clean_title(self, title: str) -> str:
        without_feat = _FEAT_PATTERN.sub("", title)
        without_parens = _PAREN_OR_BRACKET.sub(" ", without_feat)
        simplified = self._first_colon_segment(without_parens)
        return _MULTI_SPACE.sub(" ", simplified).strip(" -")

    def _first_colon_segment(self, title: str) -> str:
        parts = [part.strip() for part in _COLON_SPLIT.split(title) if part.strip()]
        if len(parts) == 0:
            return title.strip()
        return parts[0]

    def _quoted_phrase(self, title: str) -> str:
        for pattern in (_QUOTED_DOUBLE, _QUOTED_GUILLEMETS):
            match = pattern.search(title)
            if match is not None:
                return _MULTI_SPACE.sub(" ", match.group(1)).strip()
        return ""

    def _aria_hint(self, title: str) -> str:
        quoted = self._quoted_phrase(title)
        if quoted != "":
            return quoted
        match = _ACT_ARIA.search(title)
        if match is None:
            return ""
        return _MULTI_SPACE.sub(" ", match.group(1)).strip(" -:")

    def _fold_accents(self, value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value)
        return "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )

    def _join(self, *parts: str) -> str:
        joined = " ".join(part.strip() for part in parts if part.strip() != "")
        return _MULTI_SPACE.sub(" ", joined).strip()
