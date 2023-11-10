from django.http import HttpResponse
from django.shortcuts import render
from .forms import BookingForm
from .models import Menu, Category,Cart
from rest_framework import generics
from .serializers import MenuItemSerializer, CategorySerializer,RatingSerializer,CartSerializer
from rest_framework.pagination import PageNumberPagination
from .models import Rating
from rest_framework import permissions
from django.contrib.auth.models import User,Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from django.shortcuts import get_object_or_404

class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow managers to create, update, or delete menu items.
    """

    def has_permission(self, request, view):
       if request.method == 'GET':
          return True
       elif request.method in permissions.SAFE_METHODS:
          return request.user and request.user.groups.filter(name='manager').exists()
       return False



class RatingsView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def get_permissions(self):
        if(self.request.method=='GET'):
            return []

        return [IsAuthenticated()]

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
    permission_classes = [IsManagerOrReadOnly]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]  


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def manager_users(request):
    if request.method == 'GET':
        # Retrieve all users in the 'manager' group
        managers = User.objects.filter(groups__name='Manager')
        manager_data = [{'id': Manager.id, 'username': Manager.username} for Manager in managers]
        return Response(manager_data)

    elif request.method == 'POST':
        # Assign the user in the payload to the 'manager' group
        try:
            user_id = request.data['user_id']
            user = User.objects.get(pk=user_id)
        except (KeyError, User.DoesNotExist):
            return Response({'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)

        manager_group, created = Group.objects.get_or_create(name='Manager')
        user.groups.add(manager_group)
        return Response(status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def remove_manager_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    manager_group = get_object_or_404(Group, name='Manager')
    user.groups.remove(manager_group)
    return Response(status=status.HTTP_200_OK)



@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def delivery_crew_users(request):
    # Similar implementation for 'delivery_crew' group
    if request.method == 'GET':
        # Retrieve all users in the 'delivery_crew' group
        delivery_crew = User.objects.filter(groups__name='Delivery_crew')
        delivery_crew_data = [{'id': user.id, 'username': user.username} for user in delivery_crew]
        return Response(delivery_crew_data)

    elif request.method == 'POST':
        # Assign the user in the payload to the 'delivery_crew' group
        try:
            user_id = request.data['user_id']
            user = User.objects.get(pk=user_id)
        except (KeyError, User.DoesNotExist):
            return Response({'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)

        delivery_crew_group, created = Group.objects.get_or_create(name='Delivery_crew')
        user.groups.add(delivery_crew_group)
        return Response(status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def remove_delivery_crew_user(request, user_id):
    # Remove the user with the given user_id from the 'delivery_crew' group
    user = get_object_or_404(User, pk=user_id)
    delivery_crew_group = get_object_or_404(Group, name='Delivery_crew')
    user.groups.remove(delivery_crew_group)
    return Response(status=status.HTTP_200_OK)


class CartMenuItemsView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # Delete all menu items created by the current user
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)