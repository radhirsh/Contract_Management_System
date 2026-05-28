from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clauses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clause',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to='clauses/'),
        ),
    ]
