"""Clear-chat boundary over an atomic lifecycle store."""
from app.services.conversation.contracts import (
    ClearResult, ConversationError, ConversationKey, GameScope, WorldResult,
)
from app.services.conversation.ports import LifecycleStore
from pydantic import TypeAdapter


class Lifecycle:
    """Validate a clear request and delegate its atomic effects to the store."""

    def __init__(self, store: LifecycleStore) -> None:
        if not callable(getattr(store, 'clear', None)):
            raise TypeError('lifecycle store must implement clear')
        self._store = store

    def clear(self, key: ConversationKey) -> ClearResult | ConversationError:
        try:
            if not isinstance(key, ConversationKey):
                raise TypeError('clear requires a ConversationKey')
            detached_key = ConversationKey.model_validate(key.model_dump(mode='json'))
        except (TypeError, ValueError):
            return ConversationError(code='INVALID_INPUT', stage='lifecycle.clear', retryable=False,
                safe_detail='Clear requires a valid conversation identity.')
        return self._store.clear(detached_key)

    def new_game(self, expected_scope: GameScope) -> WorldResult | ConversationError:
        """Reset the expected active scope through the atomic lifecycle store."""
        try:
            detached_scope = TypeAdapter(GameScope).validate_python(expected_scope)
        except (TypeError, ValueError):
            return ConversationError(code='INVALID_INPUT', stage='lifecycle.new_game', retryable=False,
                safe_detail='New game requires the current world identity.')
        reset = getattr(self._store, 'new_game', None)
        if not callable(reset):
            return ConversationError(code='INTERNAL_FAILURE', stage='lifecycle.new_game', retryable=False,
                safe_detail='The lifecycle store cannot reset this world.')
        return reset(detached_scope)
