from ytpd.domain.playlist_resolve_result import PlaylistResolveResult
from ytpd.domain.source_kind import SourceKind
from ytpd.resolve.deezer_resolver import DeezerResolver
from ytpd.resolve.unsupported_source_url_error import UnsupportedSourceUrlError
from ytpd.resolve.url_classifier import UrlClassifier
from ytpd.resolve.youtube_resolver import YoutubeResolver


class SourcePlaylistResolver:
    """Classify a URL and dispatch to the matching playlist resolver."""

    def __init__(
        self,
        classifier: UrlClassifier,
        youtube_resolver: YoutubeResolver,
        deezer_resolver: DeezerResolver,
    ) -> None:
        self._classifier = classifier
        self._youtube_resolver = youtube_resolver
        self._deezer_resolver = deezer_resolver

    def resolve(self, url: str) -> PlaylistResolveResult:
        """Resolve ``url`` through the classifier and registered source handlers."""
        source_kind = self._classifier.classify(url)
        if source_kind is SourceKind.YOUTUBE_PLAYLIST:
            return self._youtube_resolver.resolve(url, source_kind)
        if source_kind is SourceKind.YOUTUBE_VIDEO:
            return self._youtube_resolver.resolve(url, source_kind)
        if source_kind is SourceKind.DEEZER_PLAYLIST:
            return self._deezer_resolver.resolve(url, source_kind)
        if source_kind is SourceKind.UNKNOWN:
            raise UnsupportedSourceUrlError("unsupported source kind: unknown")
        unreachable: never = source_kind
        raise UnsupportedSourceUrlError(f"unsupported source kind: {unreachable}")
