from src.api.v1.schemas.auth import Authenticate, Authenticated
def try_authenticate(authenticate: Authenticate):
    return Authenticated(result='Ok')