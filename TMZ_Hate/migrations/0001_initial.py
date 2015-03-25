# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Entities',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entity_text', models.TextField()),
                ('entity_type', models.TextField()),
                ('relevance', models.FloatField()),
                ('sentiment', models.CharField(max_length=15)),
                ('sentiment_score', models.FloatField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
