# Generated by Django 2.0.8 on 2018-08-08 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('safe', '0002_auto_20180730_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multisigtransaction',
            name='nonce',
            field=models.BigIntegerField(),
        ),
    ]
