from ytpd.domain.lm_studio_match_choice import LmStudioMatchChoice
from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.track_ref import TrackRef
from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_match_json_parser import LmStudioMatchJsonParser
from ytpd.lmstudio.lm_studio_match_structured_format import (
    LmStudioMatchStructuredFormat,
)
from ytpd.lmstudio.lm_studio_runtime_coordinator import LmStudioRuntimeCoordinator
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.ports.lm_studio_http_transport import LmStudioHttpTransport
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime

_SYSTEM_PROMPT = (
    "/no_think\n"
    "You match a music track to one YouTube search candidate. "
    "Pick the best candidate_index (0-based) or null if none fit."
)
_VERIFY_SYSTEM_PROMPT = (
    "/no_think\n"
    "You verify one YouTube match for a music track. "
    "Set candidate_index to 0 to accept, or null to reject."
)


class HttpLmStudioClient:
    """LM Studio client that picks a YouTube candidate via chat completion."""

    def __init__(
        self,
        transport: LmStudioHttpTransport,
        settings: LmStudioSettings,
        model_runtime: LmStudioModelRuntime | None = None,
    ) -> None:
        self._transport = transport
        self._settings = settings
        self._model_runtime = model_runtime or LmStudioRuntimeCoordinator(settings)
        self._model_ready = False
        self._parser = LmStudioMatchJsonParser()
        self._structured = LmStudioMatchStructuredFormat()

    def choose_match(
        self,
        track: TrackRef,
        candidates: list[MatchCandidate],
        rejection_context: str | None = None,
    ) -> LmStudioMatchChoice:
        """Ask LM Studio which candidate index fits the track."""
        if len(candidates) == 0:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message="aucun candidat pour le LLM",
            )
        try:
            self._ensure_model_ready()
            response = self._transport.post_chat(
                self._settings.model,
                _SYSTEM_PROMPT,
                self._user_prompt(track, candidates, rejection_context),
                self._structured.response_format(),
            )
            return self._parser.parse(response.content, len(candidates))
        except LmStudioError as error:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message=str(error),
            )

    def verify_match(
        self,
        track: TrackRef,
        candidate: MatchCandidate,
    ) -> LmStudioMatchChoice:
        """Ask a second LLM pass to confirm or reject one chosen candidate."""
        try:
            self._ensure_model_ready()
            response = self._transport.post_chat(
                self._settings.model,
                _VERIFY_SYSTEM_PROMPT,
                (
                    "/no_think\n"
                    f"Title: {track.title}\nArtist: {track.artist}\n"
                    f"Duration: {track.duration_sec}\n"
                    f"Candidate: {candidate.title} | {candidate.channel} | "
                    f"{candidate.duration_sec}s | {candidate.youtube_url}"
                ),
                self._structured.response_format(),
            )
            return self._parser.parse(response.content, 1)
        except LmStudioError as error:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message=str(error),
            )

    def _ensure_model_ready(self) -> None:
        if self._model_ready:
            return
        self._model_runtime.ensure_ready()
        models = self._transport.get_models()
        if self._settings.model not in models.model_ids:
            raise LmStudioError(
                f"modèle LM Studio introuvable: {self._settings.model}"
            )
        self._model_ready = True

    def _user_prompt(
        self,
        track: TrackRef,
        candidates: list[MatchCandidate],
        rejection_context: str | None,
    ) -> str:
        lines = [
            "/no_think",
            f"Title: {track.title}",
            f"Artist: {track.artist}",
            f"Duration: {track.duration_sec}",
        ]
        if rejection_context is not None and rejection_context.strip() != "":
            lines.append(
                "Previously rejected because: "
                f"{rejection_context.strip()}. "
                "Prefer the closest remaining duration/artist match."
            )
        lines.append("Candidates:")
        for index, candidate in enumerate(candidates):
            lines.append(
                f"{index}. {candidate.title} | {candidate.channel} | "
                f"{candidate.duration_sec}s | {candidate.youtube_url}"
            )
        return "\n".join(lines)
