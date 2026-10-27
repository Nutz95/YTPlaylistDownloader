_DPAPI_HINT = (
    " Hint: close Brave completely, or set youtube_cookies_file to a Netscape "
    "cookies.txt export (Get cookies.txt LOCALLY while logged into YouTube)."
)


class YtdlpDownloadErrorHint:
    """Append operator hints for known yt-dlp cookie / DPAPI failures."""

    def enrich(self, detail: str) -> str:
        """Return ``detail`` plus a DPAPI/cookies hint when applicable."""
        lowered = detail.casefold()
        if "dpapi" in lowered or "failed to decrypt" in lowered:
            if _DPAPI_HINT.strip() not in detail:
                return detail.rstrip() + _DPAPI_HINT
        return detail
