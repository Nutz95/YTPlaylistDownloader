from pathlib import Path

from tests.fakes.fake_deezer_api_client import FakeDeezerApiClient
from tests.fakes.fake_deezer_http_transport import FakeDeezerHttpTransport
from ytpd.domain.deezer_track_entry import DeezerTrackEntry
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.resolve.deezer_playlist_api_client import DeezerPlaylistApiClient
from ytpd.resolve.deezer_playlist_id_parser import DeezerPlaylistIdParser
from ytpd.resolve.deezer_resolver import DeezerResolver
from ytpd.resolve.deezer_tracks_json_parser import DeezerTracksJsonParser

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_playlist_id_parser_reads_numeric_id() -> None:
    assert (
        DeezerPlaylistIdParser().parse(
            "https://www.deezer.com/en/playlist/908622995"
        )
        == "908622995"
    )


def test_tracks_parser_paginates_via_next_url() -> None:
    parser = DeezerTracksJsonParser()
    page1 = parser.parse_text(
        (_FIXTURES / "deezer_tracks_page1.json").read_text(encoding="utf-8")
    )
    page2 = parser.parse_text(
        (_FIXTURES / "deezer_tracks_page2.json").read_text(encoding="utf-8")
    )
    assert len(page1.tracks) == 1
    assert page1.next_url is not None
    assert page1.tracks[0].deezer_id == "101"
    assert page2.next_url is None
    assert page2.tracks[0].artist == "Other Artist"


def test_deezer_resolver_maps_tracks_to_resolved_phase() -> None:
    url = "https://link.deezer.com/s/demo"
    client = FakeDeezerApiClient(
        {
            url: [
                DeezerTrackEntry(
                    deezer_id="101",
                    title="Track One",
                    artist="Deezer Artist",
                    duration_sec=200,
                )
            ]
        }
    )
    result = DeezerResolver(client).resolve(url, SourceKind.DEEZER_PLAYLIST)
    assert result.source_kind is SourceKind.DEEZER_PLAYLIST
    assert len(result.tracks) == 1
    assert result.tracks[0].phase is TrackPhase.RESOLVED
    assert result.tracks[0].deezer_id == "101"
    assert result.tracks[0].youtube_url is None


def test_playlist_api_client_short_link_and_pagination() -> None:
    short = "https://link.deezer.com/s/demo"
    long_url = "https://www.deezer.com/playlist/42"
    page1_url = "https://api.deezer.com/playlist/42/tracks"
    page2_url = "https://api.deezer.com/playlist/42/tracks?index=1"
    transport = FakeDeezerHttpTransport(
        text_by_url={
            page1_url: (_FIXTURES / "deezer_tracks_page1.json").read_text(
                encoding="utf-8"
            ),
            page2_url: (_FIXTURES / "deezer_tracks_page2.json").read_text(
                encoding="utf-8"
            ),
        },
        final_url_by_short={short: long_url},
    )
    client = DeezerPlaylistApiClient(transport)
    tracks = client.fetch_playlist_tracks(short)
    assert [item.deezer_id for item in tracks] == ["101", "202"]
