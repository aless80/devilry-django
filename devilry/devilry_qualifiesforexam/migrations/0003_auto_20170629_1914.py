# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-06-29 17:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('devilry_qualifiesforexam', '0002_auto_20170223_1112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='createtime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]