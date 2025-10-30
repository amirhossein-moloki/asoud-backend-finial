from channels.db import database_sync_to_async

async def validate_user(scope):
    # to avoid app ready error
    from rest_framework.authtoken.models import Token
    query_string = scope["query_string"].decode("utf-8")
    token_key = None

    # Parse the query string to get the token
    for param in query_string.split("&"):
        if param.startswith("token="):
            token_key = param.split("=")[1]
            break

    if not token_key:
        return None

    # Validate the token and fetch the user
    try:
        token = await database_sync_to_async(Token.objects.get)(key=token_key)
        get_user = database_sync_to_async(lambda t: t.user)
        user = await get_user(token)
        
        return user
    except Token.DoesNotExist:
        return None
