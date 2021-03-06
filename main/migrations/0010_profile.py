# Generated by Django 3.2.2 on 2021-07-12 17:37

from django.db import migrations, models
import main.validators


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_job__walltime'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orcid_id', models.CharField(max_length=19, validators=[main.validators.validate_orcid_id], verbose_name='ORCID iD')),
            ],
        ),
    ]
