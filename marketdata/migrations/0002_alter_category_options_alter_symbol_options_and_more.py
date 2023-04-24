# Generated by Django 4.1.7 on 2023-03-05 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketdata', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='symbol',
            options={'ordering': ('ticker',)},
        ),
        migrations.RenameField(
            model_name='symbol',
            old_name='last_ask',
            new_name='ask',
        ),
        migrations.RenameField(
            model_name='symbol',
            old_name='last_bid',
            new_name='bid',
        ),
        migrations.RenameField(
            model_name='symbol',
            old_name='code',
            new_name='ticker',
        ),
        migrations.RemoveField(
            model_name='symbol',
            name='base_currency',
        ),
        migrations.RemoveField(
            model_name='symbol',
            name='pip_position',
        ),
        migrations.RemoveField(
            model_name='symbol',
            name='quote_currency',
        ),
        migrations.RemoveField(
            model_name='symbol',
            name='swap_long',
        ),
        migrations.RemoveField(
            model_name='symbol',
            name='swap_short',
        ),
        migrations.AddField(
            model_name='symbol',
            name='pip_size',
            field=models.FloatField(default=1),
        ),
        migrations.AddField(
            model_name='symbol',
            name='standard_lot',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='symbol',
            name='tick_size',
            field=models.FloatField(default=1),
        ),
    ]
