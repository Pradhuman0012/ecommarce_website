from django.contrib import admin
from django.urls import path
from home import views 
urlpatterns = [
    path('', views.homeView, name='homeView'),
    path('about/', views.about, name='about'),
    path('searchBook/', views.searchBook, name='searchBook'),
    path('tranding/', views.tranding, name='tranding'),
    path('shop/<int:pk>/', views.shopView, name='shopView'),
    path('checkout/', views.checkout, name='checkout'),
    path('login/', views.login, name='login'),
    path('storedata/', views.storedata, name='storedata')
]