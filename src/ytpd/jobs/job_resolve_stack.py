from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_store import JobStore
from ytpd.ports.deezer_api_client import DeezerApiClient
from ytpd.ports.ytdlp_flat_playlist_client import YtdlpFlatPlaylistClient
from ytpd.resolve.deezer_resolver import DeezerResolver
from ytpd.resolve.source_playlist_resolver import SourcePlaylistResolver
from ytpd.resolve.url_classifier import UrlClassifier
from ytpd.resolve.youtube_resolver import YoutubeResolver


class JobResolveStack:
    """Wire classifier + YouTube/Deezer clients into a job resolve service."""

    def __init__(
        self,
        job_store: JobStore,
        ytdlp_client: YtdlpFlatPlaylistClient,
        deezer_client: DeezerApiClient,
    ) -> None:
        self.resolve_service = JobResolveService(
            job_store,
            SourcePlaylistResolver(
                UrlClassifier(),
                YoutubeResolver(ytdlp_client),
                DeezerResolver(deezer_client),
            ),
        )
