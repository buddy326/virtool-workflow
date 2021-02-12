import logging
from inspect import signature
from typing import List, Any, Callable

from virtool_workflow import utils
from virtool_workflow.execution.hooks.hooks import Hook
from virtool_workflow.fixtures.scope import FixtureScope

logger = logging.getLogger(__name__)


class FixtureHook(Hook):
    """A Hook which binds fixtures to it's callback functions before invoking them."""

    def _callback(self, callback_: Callable):
        """Register a callback function, skipping parameter validation"""
        logger.debug(f"Registered callback {callback_} onto hook {self.name}")
        callback_ = utils.coerce_to_coroutine_function(callback_)
        self.callbacks.append(callback_)
        return callback_

    async def trigger(self, scope: FixtureScope, *args, **kwargs) -> List[Any]:
        """Bind fixtures from `scope` to each callback function and invoke them."""
        if "scope" not in scope:
            scope["scope"] = scope

        async def _bind(callback_: Callable):
            logger.debug(f"Binding fixtures to callback {callback_}")
            return await scope.bind(callback_, strict=not args)

        _callbacks = [await _bind(callback) for callback in self.callbacks]
        _callbacks = [utils.coerce_coroutine_function_to_accept_any_parameters(callback)
                      if len(signature(callback).parameters) == 0 else callback
                      for callback in _callbacks]

        return await self._trigger(_callbacks, *args, **kwargs)
