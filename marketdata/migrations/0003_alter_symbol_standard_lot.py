# Generated by Django 4.1.7 on 2023-03-05 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketdata', '0002_alter_category_options_alter_symbol_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='symbol',
            name='standard_lot',
            field=models.IntegerField(default=100),
        ),
    ]
