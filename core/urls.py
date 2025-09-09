from django.urls import path
from core import views

urlpatterns = [
 path('', views.login_view, name='login'),
 path('inicio/', views.inicio, name='inicio'),
 path('ideias/nova/', views.cadastrar_ideia, name='cadastrar_ideia'),
 path('ideias/<int:pk>/', views.detalhe_ideia, name='detalhe_ideia'),
 path('ideias/minhas-equipes/', views.ideias_minhas_equipes, name='ideias_minhas_equipes'),
]