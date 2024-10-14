# Generated by Django 5.1.2 on 2024-10-10 14:38
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("report", "0001_initial"),
    ]
    operations = [
        migrations.AlterField(
            model_name="report",
            name="reason",
            field=models.CharField(
                choices=[
                    ("spam", "스팸"),
                    ("abuse", "욕설/비방"),
                    ("adult", "성인 콘텐츠"),
                    ("other", "기타"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "처리 대기"),
                    ("in_progress", "처리 중"),
                    ("resolved", "해결됨"),
                    ("rejected", "반려됨"),
                ],
                default="pending",
            ),
        ),
    ]
