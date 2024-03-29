# Generated by Django 4.1.7 on 2023-03-11 14:28

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategies', '0003_alter_volatility_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='volatility',
            name='log_periods',
            field=models.PositiveIntegerField(default=20),
        ),
        migrations.AlterField(
            model_name='volatility',
            name='trigger',
            field=models.FloatField(default=0.25, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
