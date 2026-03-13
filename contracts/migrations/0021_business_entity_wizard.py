# Generated migration for business entity wizard

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contracts', '0020_alter_auditlog_action_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='business_entity_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('PT', 'Perusahaan Terbatas (PT)'),
                    ('CV', 'Commanditaire Vennootschap (CV)'),
                    ('PERORANGAN', 'Perorangan')
                ],
                max_length=20,
                null=True,
                verbose_name='Business Entity Type'
            ),
        ),
        migrations.CreateModel(
            name='BusinessEntityDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(
                    choices=[
                        ('AKTA_PENDIRIAN', 'Akta Pendirian'),
                        ('NPWP', 'NPWP'),
                        ('NIB', 'NIB (Nomor Induk Berusaha)'),
                        ('KTP_PENANGGUNG_JAWAB', 'KTP Penanggung Jawab'),
                        ('PERIZINAN_LAINNYA', 'Perizinan Lainnya'),
                        ('KTP', 'KTP')
                    ],
                    max_length=50,
                    verbose_name='Document Type'
                )),
                ('document', models.FileField(upload_to='business_entity_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('contract', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='business_entity_documents',
                    to='contracts.contract'
                )),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ['document_type', 'uploaded_at'],
            },
        ),
    ]
