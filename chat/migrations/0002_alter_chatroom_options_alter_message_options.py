# Generated by Django 5.1.1 on 2024-10-04 11:14
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]
    operations = [
        migrations.AlterModelOptions(
            name="chatroom",
            options={"verbose_name": "Chat Room", "verbose_name_plural": "Chat Rooms"},
        ),
        migrations.AlterModelOptions(
            name="message",
            options={"verbose_name": "Message", "verbose_name_plural": "Messages"},
        ),
    ]
