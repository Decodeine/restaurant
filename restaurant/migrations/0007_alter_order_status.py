# Generated by Django 4.2.5 on 2023-11-11 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0006_alter_cart_created_at_alter_cart_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.BooleanField(),
        ),
    ]
