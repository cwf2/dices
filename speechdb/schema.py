from drf_spectacular.openapi import AutoSchema


class PublicReadAutoSchema(AutoSchema):
    """AutoSchema that omits security requirements from generated docs.

    All endpoints here are read-only (ListAPIView/RetrieveAPIView) and
    publicly accessible despite IsAuthenticatedOrReadOnly, which only
    restricts writes that don't exist on these views. Without this
    override, drf-spectacular shows misleading auth-required padlocks
    on every endpoint in the Swagger UI.
    """

    def get_auth(self):
        return []
