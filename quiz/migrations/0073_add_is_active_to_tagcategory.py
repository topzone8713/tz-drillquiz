# Generated manually for adding is_active field to TagCategory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0072_assign_existing_tags_to_it_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='tagcategory',
            name='is_active',
            field=models.BooleanField(default=True, help_text='비활성화된 카테고리는 UI에서 숨겨집니다.', verbose_name='활성화', db_index=True),
        ),
    ]

