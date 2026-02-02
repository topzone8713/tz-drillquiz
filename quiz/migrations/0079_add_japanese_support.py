# Generated manually for Japanese language support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0078_add_multilingual_fields_to_tagcategory"),
    ]

    operations = [
        # Question 모델에 일본어 필드 추가
        migrations.AddField(
            model_name="question",
            name="title_ja",
            field=models.CharField(
                blank=True, max_length=200, verbose_name="일본어 제목"
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="content_ja",
            field=models.TextField(blank=True, verbose_name="일본어 문제 내용"),
        ),
        migrations.AddField(
            model_name="question",
            name="answer_ja",
            field=models.TextField(blank=True, verbose_name="일본어 정답"),
        ),
        migrations.AddField(
            model_name="question",
            name="explanation_ja",
            field=models.TextField(blank=True, null=True, verbose_name="일본어 설명"),
        ),
        migrations.AddField(
            model_name="question",
            name="is_ja_complete",
            field=models.BooleanField(default=False, verbose_name="일본어 완성"),
        ),
        # Question 모델 인덱스 추가
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["title_ja"], name="quiz_questi_title_j_abc123_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["content_ja"], name="quiz_questi_content_abc123_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["is_ja_complete"], name="quiz_questi_is_ja_c_abc123_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["created_language", "is_ja_complete"], name="quiz_questi_created_abc123_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["source_id", "title_ja"], name="quiz_questi_source__abc123_idx"
            ),
        ),
        # TagCategory 모델에 일본어 필드 추가 (이미 name_ja는 있지만 is_ja_complete 확인 필요)
        migrations.AddField(
            model_name="tagcategory",
            name="is_ja_complete",
            field=models.BooleanField(default=False, verbose_name="일본어 완성"),
        ),
        # Exam 모델에 일본어 필드 추가
        migrations.AddField(
            model_name="exam",
            name="title_ja",
            field=models.CharField(
                blank=True, max_length=200, verbose_name="일본어 제목"
            ),
        ),
        migrations.AddField(
            model_name="exam",
            name="description_ja",
            field=models.TextField(blank=True, null=True, verbose_name="일본어 설명"),
        ),
        migrations.AddField(
            model_name="exam",
            name="is_ja_complete",
            field=models.BooleanField(default=False, verbose_name="일본어 완성"),
        ),
        # Exam 모델 인덱스 추가
        migrations.AddIndex(
            model_name="exam",
            index=models.Index(
                fields=["title_ja"], name="quiz_exam_title_j_abc123_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="exam",
            index=models.Index(
                fields=["is_ja_complete"], name="quiz_exam_is_ja_c_abc123_idx"
            ),
        ),
        # Study 모델에 일본어 필드 추가
        migrations.AddField(
            model_name="study",
            name="title_ja",
            field=models.CharField(
                blank=True, max_length=200, verbose_name="일본어 제목"
            ),
        ),
        migrations.AddField(
            model_name="study",
            name="goal_ja",
            field=models.TextField(blank=True, verbose_name="일본어 목표"),
        ),
        migrations.AddField(
            model_name="study",
            name="is_ja_complete",
            field=models.BooleanField(default=False, verbose_name="일본어 완성"),
        ),
        # Study 모델 인덱스 추가
        migrations.AddIndex(
            model_name="study",
            index=models.Index(
                fields=["is_ja_complete"], name="quiz_study_is_ja_c_abc123_idx"
            ),
        ),
        # created_language choices에 일본어 추가
        migrations.AlterField(
            model_name="exam",
            name="created_language",
            field=models.CharField(
                choices=[
                    ("ko", "한국어"),
                    ("en", "English"),
                    ("es", "Español"),
                    ("zh", "中文"),
                    ("ja", "日本語"),
                ],
                default="ko",
                max_length=2,
                verbose_name="생성 언어",
            ),
        ),
        migrations.AlterField(
            model_name="study",
            name="created_language",
            field=models.CharField(
                choices=[
                    ("ko", "한국어"),
                    ("en", "English"),
                    ("es", "Español"),
                    ("zh", "中文"),
                    ("ja", "日本語"),
                ],
                default="ko",
                max_length=2,
                verbose_name="생성 언어",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="created_language",
            field=models.CharField(
                choices=[
                    ("ko", "한국어"),
                    ("en", "English"),
                    ("es", "Español"),
                    ("zh", "中文"),
                    ("ja", "日本語"),
                ],
                default="en",
                max_length=2,
                verbose_name="생성 언어",
            ),
        ),
        migrations.AlterField(
            model_name="tagcategory",
            name="created_language",
            field=models.CharField(
                choices=[
                    ("ko", "한국어"),
                    ("en", "English"),
                    ("es", "Español"),
                    ("zh", "中文"),
                    ("ja", "日本語"),
                ],
                default="en",
                max_length=2,
                verbose_name="생성 언어",
            ),
        ),
    ]






