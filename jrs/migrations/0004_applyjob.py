# Generated by Django 4.2 on 2023-04-17 02:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jrs', '0003_job'),
    ]

    operations = [
        migrations.CreateModel(
            name='applyjob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=200)),
                ('resume', models.ImageField(upload_to='')),
                ('apply_date', models.DateField()),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Received', 'Received'), ('Rejected', 'Rejected')], default='Pending', max_length=20)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jrs.student')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jrs.job')),
            ],
        ),
    ]
