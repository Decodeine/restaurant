from django.http import HttpResponse
from django.shortcuts import render
from .forms import BookingForm
from .models import Menu, Category
from rest_framework import generics, filters
from .serializers import MenuItemSerializer, CategorySerializer
from rest_framework.pagination import PageNumberPagination

# Create your views here.
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def book(request):
    form = BookingForm()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
    context = {'form': form}
    return render(request, 'book.html', context)

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class YourPaginationClass(PageNumberPagination):
    page_size = 5  # Number of items per page
    page_size_query_param = 'page'
    max_page_size = 50

class MenuItemsView(generics.ListCreateAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'inventory']
    filterset_fields = ['price', 'inventory']
    search_fields = ['name']
    pagination_class = YourPaginationClass

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuItemSerializer
