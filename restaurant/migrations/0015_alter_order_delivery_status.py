# Generated by Django 4.2.5 on 2023-12-14 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0014_order_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery_status',
            field=models.CharField(choices=[('Delivery', 'Delivery'), ('SelfPickUp', 'Self Pick Up'), ('Pending', 'Pending Assignment')], max_length=20),
        ),
    ]
