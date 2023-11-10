from django.http import HttpResponse
from django.shortcuts import render
from .forms import BookingForm
from .models import Menu, Category,Cart,Order,OrderItem
from rest_framework import generics
from .serializers import MenuItemSerializer, CategorySerializer,RatingSerializer,CartSerializer,OrderSerializer,OrderItemSerializer
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
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        elif request.method in permissions.SAFE_METHODS:
            return request.user and request.user.groups.filter(name='manager').exists()
        return False

class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='delivery_crew').exists()
    
class IsOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the order
        return obj.user == request.user





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
        # Check if a cart entry already exists for the given menu item and user
        existing_cart_entry = Cart.objects.filter(user=self.request.user, menu=serializer.validated_data['menu']).first()

        if existing_cart_entry:
            # Update the quantity if the cart entry already exists
            existing_cart_entry.quantity += serializer.validated_data['quantity']
            existing_cart_entry.save()
            serializer = CartSerializer(existing_cart_entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create a new cart entry if it doesn't exist
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        # Delete all menu items created by the current user
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            # Manager can see orders for all users
            return Order.objects.all()
        else:
            # Customers can see only their orders
            return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        # Retrieve current cart items for the current user
        cart_items = Cart.objects.filter(user=self.request.user)

        # Check if the cart is not empty
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total price based on cart items
        total_price = sum(cart_item.price for cart_item in cart_items)

        # Create a new order
        order = Order.objects.create(
            user=self.request.user,
            status=True,  # Set your default status here
            total=total_price,  # Set your default total here
            # You may need to set other fields like delivery_crew, date, etc.
        )

        # Create order items based on cart items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu=cart_item.menu,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price,
            )

        # Delete all items from the cart for this user
        cart_items.delete()

        # Set the created order as the serializer instance
        serializer.instance = order

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner | IsManagerOrReadOnly | IsDeliveryCrew]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Check if a manager or delivery crew is updating the order
        if request.user.groups.filter(name='manager').exists():
            # Check if a delivery crew is assigned
            if 'delivery_crew' in serializer.validated_data and serializer.validated_data['delivery_crew'] is not None:
                # Check and update the status accordingly
                if serializer.validated_data.get('status') == 0:
                    # Status 0 means the order is out for delivery
                    # You may want to implement additional logic here
                    pass
                elif serializer.validated_data.get('status') == 1:
                    # Status 1 means the order has been delivered
                    # You may want to implement additional logic here
                    pass

        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        # Perform additional actions before deleting the order
        instance.delete()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the user has permission to delete the order
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Add other actions as needed

    def get_queryset(self):
      user = self.request.user
      if user.groups.filter(name='manager').exists():
        # Manager can see orders for all users
          return Order.objects.all()
      elif user.groups.filter(name='delivery_crew').exists():
        # Delivery crew can see orders assigned to them
          return Order.objects.filter(delivery_crew=user)
      else:
        # Other users can only see their own orders
         return Order.objects.filter(user=user)


