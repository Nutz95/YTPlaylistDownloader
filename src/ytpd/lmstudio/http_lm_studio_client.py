from ytpd.domain.lm_studio_match_choice import LmStudioMatchChoice
from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.track_ref import TrackRef
from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.ports.lm_studio_http_transport import LmStudioHttpTransport

_SYSTEM_PROMPT = (
    "Tu choisis le meilleur candidat YouTube pour un titre Deezer. "
    "Réponds uniquement avec l'index entier du candidat (0-based), "
    "ou NONE si aucun n'est correct."
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
        except LmStudioError as error:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message=str(error),
            )
        return self._parse_choice(response.content, len(candidates))

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

    def _parse_choice(self, content: str, count: int) -> LmStudioMatchChoice:
        token = content.strip().split()[0].upper()
        if token == "NONE":
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message="LLM: aucun candidat retenu",
            )
        try:
            index = int(token)
        except ValueError:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message="réponse LLM illisible",
            )
        if index < 0 or index >= count:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message="index LLM hors bornes",
            )
        return LmStudioMatchChoice(candidate_index=index, error_message=None)
