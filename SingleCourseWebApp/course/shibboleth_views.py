from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from urllib.parse import quote  
import logging
from pprint import pformat

# Set up logging
logger = logging.getLogger(__name__)

#Logout settings.
LOGOUT_URL = getattr(settings, 'LOGOUT_URL', '/logout/')
LOGOUT_REDIRECT_URL = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/login/')

class ShibbolethView(TemplateView):
    """
    This is here to offer a Shib protected page that we can
    route users through to login.
    """
    template_name = 'course/user_info.html'

    #@method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Django docs say to decorate the dispatch method for 
        class based views.
        https://docs.djangoproject.com/en/dev/topics/auth/
        """
        return super(ShibbolethView, self).dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        """Process the request."""
        next = self.request.GET.get('next', None)
        if next is not None:
            return redirect(next)
        return super(ShibbolethView, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(ShibbolethView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        # Add Shibboleth headers to context
        context['shib_headers'] = {
            k: v for k, v in self.request.META.items() 
        }
        return context


class ShibbolethDebugView(TemplateView):
    template_name = 'course/auth_debug.html'

    def get(self, request, *args, **kwargs):
        # Collect debug information
        debug_info = {
            'User Authentication': {
                'is_authenticated': request.user.is_authenticated,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else None,
                'email': request.user.email if request.user.is_authenticated else None,
            },
            'Session Info': {
                'session_key': request.session.session_key,
                'session_data': dict(request.session.items()),
            },
            'Shibboleth Headers': {
                key: value for key, value in request.META.items() 
                if key.startswith(('HTTP_SHIB', 'REMOTE_USER', 'Shib-', 'MAIL'))
            },
            'All Request Headers': {
                key: value for key, value in request.META.items() 
                if key.startswith('HTTP_')
            },
            'Request Details': {
                'path': request.path,
                'method': request.method,
                'is_secure': request.is_secure(),
                'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
            },
            'Shibboleth Settings': {
                'LOGIN_URL': getattr(settings, 'LOGIN_URL', None),
                'LOGOUT_URL': getattr(settings, 'LOGOUT_URL', None),
                'SHIBBOLETH_ATTRIBUTE_MAP': getattr(settings, 'SHIBBOLETH_ATTRIBUTE_MAP', None),
            }
        }

        # Log the debug information
        logger.info("Authentication Debug Information:\n%s", pformat(debug_info))

        return render(request, self.template_name, {'debug_info': debug_info})


class ShibbolethLoginView(TemplateView):
    """
    Pass the user to the Shibboleth login page with debug logging.
    """
    redirect_field_name = "target"

    def get(self, request, *args, **kwargs):
        logger.info("Starting login process...")
        
        # Log current user state
        logger.info("Current user state: authenticated=%s, user=%s", 
                   request.user.is_authenticated,
                   getattr(request.user, 'username', 'AnonymousUser'))

        # Build the target URL
        base_uri = request.build_absolute_uri('/').rstrip('/')
        target = base_uri + '/course/home/'  # Redirect to debug view after login
        
        # Get login URL
        login_endpoint = getattr(settings, 'LOGIN_URL', None)
        logger.info("Login endpoint: %s", login_endpoint)
        
        if not login_endpoint:
            error_msg = "LOGIN_URL not configured in settings"
            logger.error(error_msg)
            return HttpResponse(error_msg, status=500)

        # Construct login URL with target
        login_url = f'{login_endpoint}?target={quote(target)}'
        logger.info("Redirecting to: %s", login_url)
        
        return redirect(login_url)


class ShibbolethLogoutView(TemplateView):
    """
    Handle logout with debug logging.
    """
    redirect_field_name = "next"

    def handle_logout(self, request, *args, **kwargs):
        logger.info("Starting logout process...")
        
        # Log pre-logout state
        logger.info("Pre-logout user state: authenticated=%s, user=%s", 
                   request.user.is_authenticated,
                   getattr(request.user, 'username', 'AnonymousUser'))

        # Perform logout
        auth.logout(request)
        
        # Log post-logout state
        logger.info("Post-logout user state: authenticated=%s", 
                   request.user.is_authenticated)

        # Get target URL
        target = (
            request.GET.get(self.redirect_field_name) or 
            getattr(settings, 'LOGOUT_REDIRECT_URL', None) or 
            '/'
        )
        
        # Ensure absolute URI
        if not target.startswith('http'):
            target = request.build_absolute_uri(target)
        
        logger.info("Logout target URL: %s", target)

        # Get logout URL
        logout_url = LOGOUT_URL
        if '%s' in logout_url:
            logout_url = logout_url % quote(target)

        return redirect(logout_url)

    def get(self, request, *args, **kwargs):
        return self.handle_logout(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle_logout(request, *args, **kwargs)