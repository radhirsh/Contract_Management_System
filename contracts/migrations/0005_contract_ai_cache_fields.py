from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0004_contractcomparison_comparison_detail_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='ai_analyzed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contract',
            name='ai_extracted_text',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='contract',
            name='ai_source_file',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='contract',
            name='ai_summary',
            field=models.TextField(blank=True, default=''),
        ),
    ]
