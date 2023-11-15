from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import manager_users, remove_manager_user, delivery_crew_users, remove_delivery_crew_user



urlpatterns = [
    path('', views.home, name="home"),
    path('about/', views.about, name="about"),
    path('book/', views.book, name="book"), 
    path('bookings', views.bookings, name='bookings'),
    path('api/menu/', views.MenuItemsView.as_view(), name="MenuItemsView"),
    path('api/menu/<int:pk>', views.SingleMenuItemView.as_view()),
    path('categories', views.CategoriesView.as_view()),
    path('ratings', views.RatingsView.as_view()),
    path('api/groups/manager/users/', manager_users, name='manager_users'),
    path('api/groups/manager/users/<int:user_id>/', remove_manager_user, name='remove_manager_user'),
    path('api/groups/delivery-crew/users/', delivery_crew_users, name='delivery_crew_users'),
    path('api/groups/delivery-crew/users/<int:user_id>/', remove_delivery_crew_user, name='remove_delivery_crew_user'),
    path('api/cart/menu',views.CartMenuItemsView.as_view()),
    path('api/orders',views.OrderListView.as_view()),
    path('api/orders/<int:pk>/',views.OrderDetailView.as_view())
    # Add other URLs as needed
]
