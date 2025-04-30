import msgspec

class Test(msgspec.Struct):
    test: str


class Success(msgspec.Struct):
    message: str = msgspec.field(default="Success!")