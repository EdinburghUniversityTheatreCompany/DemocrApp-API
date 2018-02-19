# Generated by Django 2.0.2 on 2018-02-19 14:29

import Meeting.models
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('Meeting', '0006_auto_20180218_2321'),
    ]

    operations = [
        migrations.AddField(
            model_name='authtoken',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='authtoken',
            name='id',
            field=models.PositiveIntegerField(default=Meeting.models.get_new_token_id, primary_key=True, serialize=False),
        ),
    ]
