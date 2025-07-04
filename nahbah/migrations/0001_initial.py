# Generated by Django 5.1.7 on 2025-03-12 09:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Design',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(max_length=1500)),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='designs/pdfs')),
                ('image_file', models.ImageField(blank=True, null=True, upload_to='designs/images')),
                ('submission_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('contributor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='nahbah.contributor')),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nahbah.material')),
            ],
        ),
    ]
