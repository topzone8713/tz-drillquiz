# Generated manually on 2025-11-28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0084_add_es_zh_fields_to_question"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="date_of_birth",
            field=models.DateField(
                blank=True,
                help_text="사용자의 생년월일 (나이 확인 목적)",
                null=True,
                verbose_name="생년월일",
            ),
        ),
    ]

