from django.urls import path

from . import views

app_name = "prospeccao"

urlpatterns = [
    path("revendedoras/", views.RevendedoraListView.as_view(), name="revendedora_list"),
    path("revendedoras/nova/", views.RevendedoraWizardView.as_view(), name="revendedora_nova"),
    path("revendedoras/<int:pk>/", views.RevendedoraDetailView.as_view(), name="revendedora_detail"),
    path(
        "revendedoras/<int:pk>/excluir/",
        views.RevendedoraDeleteView.as_view(),
        name="revendedora_delete",
    ),
]
