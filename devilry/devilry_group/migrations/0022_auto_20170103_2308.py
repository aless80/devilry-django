# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-01-03 23:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devilry_group', '0021_merge'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='feedbackset',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='feedbackset',
            name='is_last_in_group',
        ),
    ]