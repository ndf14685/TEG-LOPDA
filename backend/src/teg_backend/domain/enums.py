from __future__ import annotations

from enum import StrEnum


class GameStatus(StrEnum):
    DRAFT = "draft"
    LOBBY = "lobby"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Role(StrEnum):
    ADMIN = "admin"
    PLAYER = "player"
    SPECTATOR = "spectator"
    AI_COMMENTATOR = "ai_commentator"
    AI_PLAYER = "ai_player"


# Roles que ocupan asiento en el orden de turnos.
# Un admin que quiera jugar debe invitarse a sí mismo con rol "player".
PLAYING_ROLES = {Role.PLAYER, Role.AI_PLAYER}


class Visibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    ADMIN = "admin"


class EventType(StrEnum):
    GAME_CREATED = "game.created"
    GAME_STARTED = "game.started"
    GAME_PAUSED = "game.paused"
    GAME_RESUMED = "game.resumed"
    GAME_FINISHED = "game.finished"
    GAME_CANCELLED = "game.cancelled"
    GAME_SNAPSHOT = "game.snapshot"  # efímero: estado completo al conectar

    PLAYER_INVITED = "player.invited"
    PLAYER_JOINED = "player.joined"
    PLAYER_READY = "player.ready"
    PLAYER_DISCONNECTED = "player.disconnected"
    PLAYER_KICKED = "player.kicked"
    PLAYER_ELIMINATED = "player.eliminated"
    PRESENCE_CHANGED = "presence.changed"  # efímero: online/reconnecting/offline

    TURN_STARTED = "turn.started"
    TURN_ENDED = "turn.ended"
    DICE_ROLLED = "dice.rolled"
    ATTACK_STARTED = "attack.started"
    ATTACK_RESOLVED = "attack.resolved"
    TERRITORY_UPDATED = "territory.updated"
    TERRITORY_CONQUERED = "territory.conquered"

    CHAT_MESSAGE = "chat.message"

    TAUNT_TRIGGERED = "taunt.triggered"
    AI_COMMENT_GENERATED = "ai.comment.generated"

    TOKEN_REGENERATED = "token.regenerated"
    ERROR = "error"  # efímero: solo hacia el cliente que causó el error


class ErrorCode(StrEnum):
    AUTH_FAILED = "AUTH_FAILED"
    NOT_FOUND = "NOT_FOUND"
    INVALID_ACTION = "INVALID_ACTION"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    NOT_YOUR_TURN = "NOT_YOUR_TURN"
    GAME_NOT_RUNNING = "GAME_NOT_RUNNING"
    GAME_STATE_CONFLICT = "GAME_STATE_CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    MESSAGE_TOO_LARGE = "MESSAGE_TOO_LARGE"
    FORBIDDEN = "FORBIDDEN"
