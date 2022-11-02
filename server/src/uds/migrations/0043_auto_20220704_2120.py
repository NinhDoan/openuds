# Generated by Django 3.2.10 on 2022-07-04 21:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uds', '0042_auto_20210628_1533'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='mfa_data',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.CreateModel(
            name='MFA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default=None, max_length=50, null=True, unique=True)),
                ('name', models.CharField(db_index=True, max_length=128)),
                ('data_type', models.CharField(max_length=128)),
                ('data', models.TextField(default='')),
                ('comments', models.CharField(max_length=256)),
                ('remember_device', models.IntegerField(default=0)),
                ('validity', models.IntegerField(default=0)),
                ('tags', models.ManyToManyField(to='uds.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='authenticator',
            name='mfa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authenticators', to='uds.mfa'),
        ),
        migrations.RemoveIndex(
            model_name='statscounters',
            name='uds_stats_c_owner_t_db894d_idx',
        ),
        migrations.RemoveIndex(
            model_name='statscounters',
            name='uds_stats_c_owner_t_a195c1_idx',
        ),
    ]
