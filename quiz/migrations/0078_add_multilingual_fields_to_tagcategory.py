# Generated manually for TagCategory multilingual support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0077_add_multilingual_fields_es_zh"),
    ]

    operations = [
        migrations.AddField(
            model_name="tagcategory",
            name="name_es",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="스페인어 카테고리명"
            ),
        ),
        migrations.AddField(
            model_name="tagcategory",
            name="name_zh",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="중국어 카테고리명"
            ),
        ),
        migrations.AddField(
            model_name="tagcategory",
            name="is_es_complete",
            field=models.BooleanField(default=False, verbose_name="스페인어 완성"),
        ),
        migrations.AddField(
            model_name="tagcategory",
            name="is_zh_complete",
            field=models.BooleanField(default=False, verbose_name="중국어 완성"),
        ),
        migrations.AddIndex(
            model_name="tagcategory",
            index=models.Index(fields=["name_es"], name="quiz_tagcat_name_es_idx"),
        ),
        migrations.AddIndex(
            model_name="tagcategory",
            index=models.Index(fields=["name_zh"], name="quiz_tagcat_name_zh_idx"),
        ),
    ]

