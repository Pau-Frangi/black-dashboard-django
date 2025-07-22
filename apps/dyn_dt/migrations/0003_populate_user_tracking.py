from django.db import migrations
from django.utils import timezone


def populate_user_tracking(apps, schema_editor):
    # Get the first superuser
    User = apps.get_model('auth', 'User')
    default_user = User.objects.filter(is_superuser=True).first()
    
    # Get all models that need updating
    models_to_update = [
        apps.get_model('dyn_dt', model_name)
        for model_name in [
            'Caja', 'Concepto', 'DenominacionEuro', 'DesgloseCaja',
            'Ejercicio', 'MovimientoBanco', 'MovimientoCaja',
            'MovimientoDinero', 'Turno'
        ]
    ]
    
    # Set default values for existing records
    now = timezone.now()
    for model in models_to_update:
        model.objects.filter(creado_en__isnull=True).update(creado_en=now)
        model.objects.filter(creado_por__isnull=True).update(creado_por=default_user)


class Migration(migrations.Migration):

    dependencies = [
        ('dyn_dt', '0002_add_user_tracking'),
    ]

    operations = [
        migrations.RunPython(populate_user_tracking, reverse_code=migrations.RunPython.noop),
    ]
