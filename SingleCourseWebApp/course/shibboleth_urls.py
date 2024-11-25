from django.urls import path
from .shibboleth_views import ShibbolethView, ShibbolethLogoutView, ShibbolethLoginView

app_name = 'shibboleth'

urlpatterns = [
    path('login/', ShibbolethLoginView.as_view(), name='login'),
    path('logout/', ShibbolethLogoutView.as_view(), name='logout'),
    path('', ShibbolethView.as_view(), name='info'),
]