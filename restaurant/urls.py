from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name="home"),
    path('about/', views.about, name="about"),
    path('book/', views.book, name="book"), 
    path('menu/', views.MenuItemsView.as_view(), name="MenuItemsView"),
    path('menu/<int:pk>', views.SingleMenuItemView.as_view()),
    path('categories', views.CategoriesView.as_view()),
    path('ratings', views.RatingsView.as_view()),
]
