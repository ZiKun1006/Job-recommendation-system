# Generated by Django 4.2 on 2023-06-13 06:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jrs', '0010_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='searchTerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search', models.CharField(max_length=100000)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jrs.student')),
            ],
        ),
    ]
