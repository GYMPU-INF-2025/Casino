import sanic

from backend.serialization import serialize, deserialize
from backend.models.responses import Success, Test

app = sanic.Sanic("Casino")

@app.post("/")
@serialize()
@deserialize()
async def hello_world(_: sanic.Request, body: Test) -> Success:
    print(body.test)
    return Success()

