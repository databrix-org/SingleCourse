from shibboleth.middleware import ShibbolethRemoteUserMiddleware

class CustomShibbolethMiddleware(ShibbolethRemoteUserMiddleware):
    header = 'HTTP_MAIL'  # Instead of using REMOTE_USER, use MAIL