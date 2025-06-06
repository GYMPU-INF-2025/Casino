import datetime
import http

import sanic
import backend.internal.serialization as serialization
import backend.utils as utils
import shared.models as models
from backend.db.queries import Queries

router = sanic.Blueprint("authentication")

WRONG_CREDENTIALS_ERROR = sanic.SanicException(
    message="Combination of username and password does not match", status_code=http.HTTPStatus.UNAUTHORIZED
)


@router.post("/login")
@serialization.serialize()
@serialization.deserialize()
async def login(_: sanic.Request, request_body: models.LoginRequest, queries: Queries) -> models.LoginResponse:
    db_user = await queries.get_user_by_username(username=request_body.username)
    if db_user is None:
        raise WRONG_CREDENTIALS_ERROR

    token = utils.generate_token(user_id=db_user.id)
    return models.LoginResponse(token=token, expires_at=datetime.datetime.now(datetime.UTC) + utils.DEFAULT_EXPIRY)
