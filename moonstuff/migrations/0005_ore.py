# Generated by Django 2.2.4 on 2019-12-11 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moonstuff', '0004_auto_20190902_2132'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ore',
            fields=[
                ('group_id', models.IntegerField()),
                ('group_name', models.CharField(max_length=255)),
                ('ore_name', models.CharField(max_length=75)),
                ('ore_id', models.IntegerField(primary_key=True, serialize=False)),
            ],
        ),
    ]
