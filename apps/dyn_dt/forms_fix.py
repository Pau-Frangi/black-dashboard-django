# This file contains the fix for the missing Ejercicio import
# Add this import to the top of your forms.py file:

from apps.dyn_dt.models import Ejercicio

# If Ejercicio model doesn't exist, you may need to:
# 1. Create the Ejercicio model in models.py
# 2. Or remove the Ejercicio reference from MovimientoCajaFilterForm
# 3. Or import it from the correct location if it's defined elsewhere
