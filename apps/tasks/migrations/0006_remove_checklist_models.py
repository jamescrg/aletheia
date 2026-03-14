# Move checklist models from tasks app to checklists app (state only, no DB changes)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_remove_checklisttemplate_is_active'),
        ('checklists', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='checklistfolder',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='checklistfolder',
                    name='parent',
                ),
                migrations.RemoveField(
                    model_name='checklistfolder',
                    name='updated_by',
                ),
                migrations.RemoveField(
                    model_name='checklistitem',
                    name='checklist',
                ),
                migrations.RemoveField(
                    model_name='checklistitem',
                    name='completed_by',
                ),
                migrations.RemoveField(
                    model_name='checklisttemplate',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='checklisttemplate',
                    name='folder',
                ),
                migrations.RemoveField(
                    model_name='checklisttemplate',
                    name='updated_by',
                ),
                migrations.RemoveField(
                    model_name='checklisttemplateitem',
                    name='template',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklistfolder',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklistfolder',
                    name='history_user',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklistfolder',
                    name='parent',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklistfolder',
                    name='updated_by',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklisttemplate',
                    name='created_by',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklisttemplate',
                    name='folder',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklisttemplate',
                    name='history_user',
                ),
                migrations.RemoveField(
                    model_name='historicalchecklisttemplate',
                    name='updated_by',
                ),
                migrations.AlterUniqueTogether(
                    name='userchecklistview',
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name='userchecklistview',
                    name='task',
                ),
                migrations.RemoveField(
                    model_name='userchecklistview',
                    name='user',
                ),
                migrations.DeleteModel(
                    name='Checklist',
                ),
                migrations.DeleteModel(
                    name='ChecklistFolder',
                ),
                migrations.DeleteModel(
                    name='ChecklistItem',
                ),
                migrations.DeleteModel(
                    name='ChecklistTemplate',
                ),
                migrations.DeleteModel(
                    name='ChecklistTemplateItem',
                ),
                migrations.DeleteModel(
                    name='HistoricalChecklistFolder',
                ),
                migrations.DeleteModel(
                    name='HistoricalChecklistTemplate',
                ),
                migrations.DeleteModel(
                    name='UserChecklistView',
                ),
            ],
            database_operations=[],
        ),
    ]
