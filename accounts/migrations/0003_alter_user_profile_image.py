# Generated by Django 5.1.1 on 2024-09-30 01:50

import imagekit.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_privacysettings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="profile_image",
            field=imagekit.models.fields.ProcessedImageField(
                blank=True, null=True, upload_to="profile_images"
            ),
        ),
    ]
