# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-01-20 17:33


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devilry_compressionutil', '0003_auto_20170119_1648'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='compressedarchivemeta',
            unique_together=set([]),
        ),
    ]
