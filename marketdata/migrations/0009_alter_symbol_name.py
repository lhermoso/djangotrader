# Generated by Django 4.1.7 on 2023-03-05 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketdata', '0008_alter_symbol_broker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='symbol',
            name='name',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
