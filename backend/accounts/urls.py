from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import AtivoAuthenticationForm

app_name = "accounts"

urlpatterns = [
    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=AtivoAuthenticationForm,
        ),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("promotoras/", views.PromotoraListView.as_view(), name="promotora_list"),
    path("promotoras/nova/", views.PromotoraCreateView.as_view(), name="promotora_nova"),
    path(
        "promotoras/<int:pk>/editar/",
        views.PromotoraUpdateView.as_view(),
        name="promotora_editar",
    ),
    path(
        "promotoras/<int:pk>/alternar/",
        views.PromotoraDesativarView.as_view(),
        name="promotora_alternar",
    ),
]
