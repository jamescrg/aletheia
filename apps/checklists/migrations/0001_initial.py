# Move checklist models from tasks app to checklists app (state only, no DB changes)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tasks', '0005_remove_checklisttemplate_is_active'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Checklist',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('name', models.CharField(max_length=100)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_created', to=settings.AUTH_USER_MODEL)),
                        ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='checklist', to='tasks.task')),
                    ],
                    options={
                        'db_table': 'app_checklist',
                    },
                ),
                migrations.CreateModel(
                    name='ChecklistFolder',
                    fields=[
                        ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('id', models.BigAutoField(primary_key=True, serialize=False)),
                        ('name', models.CharField(max_length=50)),
                        ('depth', models.IntegerField(default=0)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_created', to=settings.AUTH_USER_MODEL)),
                        ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='checklists.checklistfolder')),
                        ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'app_checklist_folder',
                        'ordering': ['name'],
                    },
                ),
                migrations.CreateModel(
                    name='ChecklistTemplate',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('name', models.CharField(max_length=100)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_created', to=settings.AUTH_USER_MODEL)),
                        ('folder', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='templates', to='checklists.checklistfolder')),
                        ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'app_checklist_template',
                        'ordering': ['name'],
                    },
                ),
                migrations.CreateModel(
                    name='HistoricalChecklistTemplate',
                    fields=[
                        ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                        ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                        ('updated_at', models.DateTimeField(blank=True, editable=False)),
                        ('name', models.CharField(max_length=100)),
                        ('history_id', models.AutoField(primary_key=True, serialize=False)),
                        ('history_date', models.DateTimeField(db_index=True)),
                        ('history_change_reason', models.CharField(max_length=100, null=True)),
                        ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                        ('created_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                        ('folder', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='checklists.checklistfolder')),
                        ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                        ('updated_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'verbose_name': 'historical checklist template',
                        'verbose_name_plural': 'historical checklist templates',
                        'db_table': 'app_checklist_template_history',
                        'ordering': ('-history_date', '-history_id'),
                        'get_latest_by': ('history_date', 'history_id'),
                    },
                    bases=(simple_history.models.HistoricalChanges, models.Model),
                ),
                migrations.CreateModel(
                    name='HistoricalChecklistFolder',
                    fields=[
                        ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                        ('updated_at', models.DateTimeField(blank=True, editable=False)),
                        ('id', models.BigIntegerField(blank=True, db_index=True)),
                        ('name', models.CharField(max_length=50)),
                        ('depth', models.IntegerField(default=0)),
                        ('history_id', models.AutoField(primary_key=True, serialize=False)),
                        ('history_date', models.DateTimeField(db_index=True)),
                        ('history_change_reason', models.CharField(max_length=100, null=True)),
                        ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                        ('created_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                        ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                        ('parent', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='checklists.checklistfolder')),
                        ('updated_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'verbose_name': 'historical checklist folder',
                        'verbose_name_plural': 'historical checklist folders',
                        'db_table': 'app_checklist_folder_history',
                        'ordering': ('-history_date', '-history_id'),
                        'get_latest_by': ('history_date', 'history_id'),
                    },
                    bases=(simple_history.models.HistoricalChanges, models.Model),
                ),
                migrations.CreateModel(
                    name='ChecklistTemplateItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('description', models.CharField(max_length=200)),
                        ('order', models.IntegerField(default=0)),
                        ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='checklists.checklisttemplate')),
                    ],
                    options={
                        'db_table': 'app_checklist_template_item',
                        'ordering': ['order', 'id'],
                    },
                ),
                migrations.CreateModel(
                    name='ChecklistItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('description', models.CharField(max_length=200)),
                        ('is_complete', models.BooleanField(default=False)),
                        ('completed_at', models.DateTimeField(blank=True, null=True)),
                        ('order', models.IntegerField(default=0)),
                        ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='checklists.checklist')),
                        ('completed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'app_checklist_item',
                        'ordering': ['order', 'id'],
                    },
                ),
                migrations.AddField(
                    model_name='checklist',
                    name='template',
                    field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='checklists.checklisttemplate'),
                ),
                migrations.AddField(
                    model_name='checklist',
                    name='updated_by',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_updated', to=settings.AUTH_USER_MODEL),
                ),
                migrations.CreateModel(
                    name='UserChecklistView',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('last_viewed_at', models.DateTimeField(auto_now=True)),
                        ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.task')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'app_user_checklist_view',
                        'unique_together': {('user', 'task')},
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
