from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem_id =  models.SmallIntegerField()
    rating = models.SmallIntegerField()


class Booking(models.Model):
   first_name = models.CharField(max_length=200)    
   last_name = models.CharField(max_length=200)
   guest_number = models.IntegerField()
   comment = models.CharField(max_length=1000)

   def __str__(self):
      return self.first_name + ' ' + self.last_name



class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)
    id = models.AutoField(primary_key=True)

    def __str__(self) -> str:
        return self.title

class Menu(models.Model):
    name = models.CharField(max_length=200,db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2,db_index=True)  # You can use validators=[MinValueValidator(2)] here if needed
    menu_item_description = models.TextField(max_length=1000,db_index=True, default='')
    inventory = models.SmallIntegerField(db_index=True)
    featured= models.BooleanField(db_index=True)

    category = models.ForeignKey(Category, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('menu', 'user')

    def save(self, *args, **kwargs):
        # Set unit_price based on the associated menu item
        self.unit_price = self.menu.price

        # Calculate total price based on quantity
        self.price = self.unit_price * self.quantity

        super().save(*args, **kwargs)


class Order(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew=models.ForeignKey(User, on_delete=models.SET_NULL, related_name='delivery_crew', null=True)
    status=models.BooleanField(db_index=True)
    total=models.DecimalField(max_digits=6,decimal_places=2)
    date=models.DateField(db_index=True)

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    menu= models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity=models.SmallIntegerField()
    unit_price=models.DecimalField(max_digits=6,decimal_places=2)
    price=models.DecimalField(max_digits=6,decimal_places=2)

    class Meta:
        unique_together=('order', 'menu')
