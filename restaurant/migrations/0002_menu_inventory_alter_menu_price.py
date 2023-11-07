# Generated by Django 4.2.5 on 2023-11-07 05:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='inventory',
            field=models.SmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='menu',
            name='price',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(2)]),
        ),
    ]
