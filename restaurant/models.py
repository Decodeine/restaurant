from django.db import models


class Booking(models.Model):
   first_name = models.CharField(max_length=200)    
   last_name = models.CharField(max_length=200)
   guest_number = models.IntegerField()
   comment = models.CharField(max_length=1000)

   def __str__(self):
      return self.first_name + ' ' + self.last_name



class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255)
    id = models.AutoField(primary_key=True)

    def __str__(self) -> str:
        return self.title

class Menu(models.Model):
    name = models.CharField(max_length=200)
    price = models.IntegerField()  # You can use validators=[MinValueValidator(2)] here if needed
    menu_item_description = models.TextField(max_length=1000, default='')
    inventory = models.SmallIntegerField()

    category = models.ForeignKey(Category, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.name
