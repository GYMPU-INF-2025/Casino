from __future__ import annotations

import msgspec

from shared.internal import Snowflake

__all__ = ("CompiledRoute", "Route")


class Route(msgspec.Struct):
    """Class representing a http endpoint.

    Authors: Christopher

    Attributes
    ----------
    method: str
        The http method this route uses.
    path_template: str
        The path this route uses. The path can have parameters that
        will be filled out when compiling the route.
        Example: "/test/{test_argument}/"
    """

    method: str
    """The HTTP method."""

    path_template: str
    """The template string used for the path."""

    def compile(self, **kwargs: str | int | bool | None | Snowflake) -> CompiledRoute:
        """Generate a formatted `CompiledRoute` for this route.

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
                val = "true"
            elif v is False:
                val = "false"
            elif v is None:
                val = "null"
            elif v is Snowflake:
                val = str(int(v))
            else:
                val = str(v)

            data[k] = val

        return CompiledRoute(route=self, compiled_path=self.path_template.format_map(data))


class CompiledRoute(msgspec.Struct):
    """Class representing a compiled route.

    Compiled routes contain the compiled path which is the normal
    path but every parameter being filled out.

    Authors: Christopher

    Attributes
    ----------
    route: Route
        The route this compiled route got created from
    compiled_path: str
        The compiled path with every parameter being filled out
    """
    route: Route
    """The route this compiled route was created from."""

    compiled_path: str
    """The compiled route path to use."""

    @property
    def method(self) -> str:
        """Return the HTTP method of this compiled route."""
        return self.route.method
