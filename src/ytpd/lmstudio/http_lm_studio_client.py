from ytpd.domain.lm_studio_match_choice import LmStudioMatchChoice
from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.track_ref import TrackRef
from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_match_json_parser import LmStudioMatchJsonParser
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.ports.lm_studio_http_transport import LmStudioHttpTransport

_SYSTEM_PROMPT = (
    "Tu es un matcheur YouTube. Réponds UNIQUEMENT avec un objet JSON "
    'strict du modèle {"candidate_index": <int|null>, "reason": "<texte>"}. '
    "candidate_index est l'index 0-based du meilleur candidat, ou null si aucun."
)


class HttpLmStudioClient:
    """LM Studio client that picks a YouTube candidate via chat completion."""

    def __init__(
        self,
        transport: LmStudioHttpTransport,
        settings: LmStudioSettings,
    ) -> None:
        self._transport = transport
        self._settings = settings
        self._model_ready = False
        self._parser = LmStudioMatchJsonParser()

    def choose_match(
        self,
        track: TrackRef,
        candidates: list[MatchCandidate],
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
                self._user_prompt(track, candidates),
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
                (
                    "Tu vérifies un match YouTube. Réponds UNIQUEMENT JSON "
                    '{"candidate_index": 0|null, "reason": "..."}. '
                    "0 = validé, null = rejeté."
                ),
                (
                    f"Titre: {track.title}\nArtiste: {track.artist}\n"
                    f"Durée: {track.duration_sec}\n"
                    f"Candidat: {candidate.title} | {candidate.channel} | "
                    f"{candidate.duration_sec}s | {candidate.youtube_url}"
                ),
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
    ) -> str:
        lines = [
            f"Titre: {track.title}",
            f"Artiste: {track.artist}",
            f"Durée: {track.duration_sec}",
            "Candidats:",
        ]
        for index, candidate in enumerate(candidates):
            lines.append(
                f"{index}. {candidate.title} | {candidate.channel} | "
                f"{candidate.duration_sec}s | {candidate.youtube_url}"
            )
        return "\n".join(lines)
