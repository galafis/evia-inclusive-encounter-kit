"""Explicit choices, reversible pause, terminal end / Escolhas, pausa e encerramento."""

from evia_journal.core import analyze as journal_analyze

from .common import bi, envelope, metric, section, unique, validate

ACTIONS = {
    "start": bi("Start", "Começar"),
    "choose": bi("Choose", "Escolher"),
    "pause": bi("Pause", "Pausar"),
    "resume": bi("Resume", "Retomar"),
    "next": bi("Next card", "Próximo cartão"),
    "skip": bi("Skip card", "Pular cartão"),
    "end": bi("End", "Encerrar"),
}
STATES = {
    "ready": bi("Not started", "Não iniciado"),
    "active": bi("Active", "Ativo"),
    "paused": bi("Paused", "Pausado"),
    "ended": bi("Ended", "Encerrado"),
}


def analyze(data):
    validate(data)
    unique(data["cards"])
    status = "ready"
    index = 0
    previous = -1
    choice = None
    completed = []
    skipped = []
    timeline = []
    public = []
    start_ms = None
    ended_ms = None
    pause_ms = None
    pause_total = 0

    def emit(at, kind, outcome):
        public.append(
            {
                "id": f"e-{len(public) + 1:04d}",
                "atMs": at,
                "sessionId": data["sessionId"],
                "kind": kind,
                "outcome": outcome,
            }
        )

    for i, event in enumerate(data["events"]):
        action = event["action"]
        at = event["atMs"]
        if at < previous or at > data["nowMs"]:
            raise ValueError(
                "Events must be ordered and not in the future / Eventos devem estar ordenados e não podem estar no futuro"
            )
        previous = at
        if action != "choose" and event["choice"] != 0:
            raise ValueError(
                "Choice belongs only to choose action / Escolha pertence somente à ação choose"
            )
        if status == "ended":
            raise ValueError("Session already ended / Encontro já encerrado")
        card = data["cards"][index]
        recorded_card = card["id"]
        selected_text = None
        if action == "end":
            if status == "paused":
                pause_total += at - pause_ms
                pause_ms = None
            status = "ended"
            ended_ms = at
            emit(at, "session-stop", "ok")
        elif action == "start" and status == "ready":
            status = "active"
            start_ms = at
            emit(at, "session-start", "ok")
            emit(at, "cue-presented", "ok")
        elif action == "pause" and status == "active":
            status = "paused"
            pause_ms = at
            emit(at, "session-pause", "interrupted")
        elif action == "resume" and status == "paused":
            pause_total += at - pause_ms
            pause_ms = None
            status = "active"
            emit(at, "observation", "ok")
        elif action == "choose" and status == "active":
            if event["choice"] >= len(card["alternatives"]):
                raise ValueError("Unknown choice / Escolha desconhecida")
            choice = event["choice"]
            selected_text = card["alternatives"][choice]
            emit(at, "observation", "ok")
        elif action in ("next", "skip") and status == "active":
            if action == "next" and choice is None:
                raise ValueError(
                    "Explicit choice required before next / Escolha explícita exigida antes de avançar"
                )
            if action == "next":
                completed.append(card["id"])
            else:
                skipped.append(card["id"])
            emit(at, "observation", "skipped" if action == "skip" else "ok")
            choice = None
            if index == len(data["cards"]) - 1:
                status = "ended"
                ended_ms = at
                emit(at, "session-stop", "ok")
            else:
                index += 1
                emit(at, "cue-presented", "ok")
        else:
            raise ValueError(
                f"Action {action} is unavailable in {status} / Ação indisponível neste estado"
            )
        timeline.append(
            {
                "event": i + 1,
                "atMs": at,
                "action": action,
                "cardId": recorded_card,
                "choice": selected_text,
                "status": status,
            }
        )
    stop = ended_ms if ended_ms is not None else data["nowMs"]
    if pause_ms is not None:
        pause_total += stop - pause_ms
    elapsed = stop - start_ms if start_ms is not None else 0
    active = max(0, elapsed - pause_total)
    journal_input = {
        "schemaVersion": 1,
        "scenarioId": data["scenarioId"],
        "source": data["source"],
        "nowMs": data["nowMs"],
        "retentionMs": data["retentionMs"],
        "events": public,
    }
    journal = journal_analyze(journal_input)
    current = data["cards"][index]
    legal = {
        "ready": ["start", "end"],
        "active": ["choose", "pause", "skip", "end"] + (["next"] if choice is not None else []),
        "paused": ["resume", "end"],
        "ended": [],
    }[status]
    return envelope(
        data,
        kind="encounter",
        summary=bi(
            "Preview an optional encounter, select how to take part, and keep pause, skip and end available. All events here are fictional.",
            "Conheça um encontro opcional, escolha como participar e mantenha disponíveis pausa, pular e encerrar. Todos os eventos aqui são fictícios.",
        ),
        metrics=[
            metric(bi("Current state", "Estado atual"), STATES[status]),
            metric(
                bi("Cards completed", "Cartões concluídos"),
                f"{len(completed)}/{len(data['cards'])}",
            ),
            metric(bi("Paused time", "Tempo em pausa"), f"{pause_total / 1000:g} s"),
            metric(bi("Skipped cards", "Cartões pulados"), len(skipped)),
        ],
        sections=[
            section(
                bi("My preferences", "Minhas preferências"),
                [bi("Preference", "Preferência"), bi("Choice", "Escolha")],
                [
                    [bi("Distance", "Distância"), data["preferences"]["distance"]],
                    [bi("Communication", "Comunicação"), data["preferences"]["communication"]],
                    [bi("Quiet place", "Local tranquilo"), data["preferences"]["quietPlace"]],
                ],
            ),
            section(
                bi(
                    "What happened, without scoring the participant",
                    "O que aconteceu, sem pontuar o participante",
                ),
                [
                    bi("Time (s)", "Tempo (s)"),
                    bi("Action", "Ação"),
                    bi("Card", "Cartão"),
                    bi("Choice", "Escolha"),
                    bi("State after action", "Estado após a ação"),
                ],
                [
                    [
                        row["atMs"] / 1000,
                        ACTIONS[row["action"]],
                        row["cardId"],
                        row["choice"] or "—",
                        STATES[row["status"]],
                    ]
                    for row in timeline
                ],
            ),
        ],
        state={
            "status": status,
            "cardIndex": index,
            "choice": choice,
            "legalActions": legal,
            "completed": completed,
            "skipped": skipped,
            "activeMs": active,
            "pausedMs": pause_total,
        },
        timeline=timeline,
        journal=journal,
        journalInput=journal_input,
        visual={
            "type": "encounter",
            "cards": data["cards"],
            "currentCard": index,
            "status": status,
        },
        cards=[
            {
                "title": card["title"],
                "steps": [card["invitation"]],
                "choices": card["alternatives"],
                "footer": bi(
                    "You may pause, skip or end. No approach or touch is required.",
                    "Você pode pausar, pular ou encerrar. Não é preciso se aproximar nem tocar.",
                ),
            }
            for card in data["cards"]
        ],
        currentInvitation=current["invitation"],
        reviewRequired=False,
    )


def artifacts(data, report):
    return {
        "participant-cards.json": report["cards"],
        "public-journal-input.json": report["journalInput"],
        "public-journal-report.json": report["journal"],
    }
