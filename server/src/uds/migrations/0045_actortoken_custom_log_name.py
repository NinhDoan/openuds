# Generated by Django 4.2.1 on 2023-05-10 22:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("uds", "0044_notification_notifier_servicetokenalias_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="actortoken",
            name="custom",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="log",
            name="name",
            field=models.CharField(default="", max_length=64),
        ),
    ]
