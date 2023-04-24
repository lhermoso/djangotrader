# Generated by Django 4.1.7 on 2023-03-05 14:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketdata', '0004_alter_category_yahoo_suffix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='symbol',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='symbols', to='marketdata.category'),
        ),
    ]
