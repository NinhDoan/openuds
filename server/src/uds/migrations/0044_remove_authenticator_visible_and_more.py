# Generated by Django 4.0 on 2022-02-08 19:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uds', '0043_clean_unused_config'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authenticator',
            name='visible',
        ),
        migrations.RemoveField(
            model_name='transport',
            name='nets_positive',
        ),
        migrations.AddField(
            model_name='authenticator',
            name='net_filtering',
            field=models.CharField(db_index=True, default='n', max_length=1),
        ),
        migrations.AddField(
            model_name='authenticator',
            name='state',
            field=models.CharField(db_index=True, default='v', max_length=1),
        ),
        migrations.AddField(
            model_name='metapool',
            name='ha_policy',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='network',
            name='authenticators',
            field=models.ManyToManyField(db_table='uds_net_auths', related_name='networks', to='uds.Authenticator'),
        ),
        migrations.AddField(
            model_name='transport',
            name='net_filtering',
            field=models.CharField(db_index=True, default='n', max_length=1),
        ),
        migrations.AlterField(
            model_name='service',
            name='token',
            field=models.CharField(blank=True, default=None, max_length=64, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='tunneltoken',
            name='ip',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='tunneltoken',
            name='ip_from',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='userservice',
            name='src_ip',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.CreateModel(
            name='ServiceTokenAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.CharField(max_length=64, unique=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='uds.service')),
            ],
        ),
        migrations.CreateModel(
            name='Notifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default=None, max_length=50, null=True, unique=True)),
                ('data_type', models.CharField(max_length=128)),
                ('data', models.TextField(default='')),
                ('name', models.CharField(default='', max_length=128)),
                ('comments', models.CharField(default='', max_length=256)),
                ('enabled', models.BooleanField(default=True)),
                ('level', models.PositiveSmallIntegerField(choices=[(1, 'Info'), (2, 'Warning'), (3, 'Error'), (4, 'Critical')], default=1)),
                ('tags', models.ManyToManyField(to='uds.Tag')),
            ],
            options={
                'db_table': 'uds_notifier',
            },
        ),
    ]
