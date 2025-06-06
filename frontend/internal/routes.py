from __future__ import annotations

import msgspec

from shared.internal import Snowflake

__all__ = ("CompiledRoute", "Route")


class Route(msgspec.Struct):
    method: str
    """The HTTP method."""

    path_template: str
    """The template string used for the path."""

    def compile(self, **kwargs: str | int | bool | None | Snowflake) -> CompiledRoute:
        """Generate a formatted [`CompiledRoute`][] for this route.

        This takes into account any URL parameters that have been passed.

        Parameters
        ----------
        **kwargs
            Any parameters to interpolate into the route path.

        Returns
        -------
        CompiledRoute
            The compiled route.
        """
        data = {}
        for k, v in kwargs.items():
            if v is True:
                v = "true"
            elif v is False:
                v = "false"
            elif v is None:
                v = "null"
            elif v is Snowflake:
                v = str(int(v))
            else:
                v = str(v)

            data[k] = v

        return CompiledRoute(route=self, compiled_path=self.path_template.format_map(data))


class CompiledRoute(msgspec.Struct):
    route: Route
    """The route this compiled route was created from."""

    compiled_path: str
    """The compiled route path to use."""

    @property
    def method(self) -> str:
        """Return the HTTP method of this compiled route."""
        return self.route.method
