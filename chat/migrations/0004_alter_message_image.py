# Generated by Django 5.1.2 on 2024-10-12 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_websocketconnection"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="chat_images/"),
        ),
    ]
