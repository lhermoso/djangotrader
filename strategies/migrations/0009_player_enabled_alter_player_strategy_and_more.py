# Generated by Django 4.1.7 on 2023-03-21 13:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketdata', '0010_symbol_country_symbol_currency'),
        ('strategies', '0008_alter_strategy_options_remove_player_log_periods_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='player',
            name='strategy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='strategies.strategy'),
        ),
        migrations.AlterField(
            model_name='player',
            name='symbol',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='marketdata.symbol'),
        ),
        migrations.AlterField(
            model_name='player',
            name='timeframe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='strategies.timeframe'),
        ),
    ]
