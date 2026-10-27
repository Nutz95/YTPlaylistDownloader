class YtpdServerCommandMatcher:
    """Detect command lines that belong to a ytpd HTTP server instance."""

    def matches(self, command_line: str) -> bool:
        """True for ``python -m ytpd`` / ``ytpd.exe``, false for yt-dlp children."""
        lowered = command_line.casefold().replace("/", "\\")
        if " -m yt_dlp" in lowered or "\\yt-dlp" in lowered:
            return False
        if " -m ytpd" in lowered:
            return True
        if "\\scripts\\ytpd.exe" in lowered or lowered.rstrip().endswith("\\ytpd.exe"):
            return True
        return False
