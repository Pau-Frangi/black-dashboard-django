#!/usr/bin/env python
"""
Script para probar la vista de carga de movimientos
"""

import os
import django
from django.test import Client
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_ajax_request():
    """Simula la petición AJAX para cargar movimientos de un ejercicio"""
    client = Client()
    
    # Crear un usuario de prueba y hacer login
    from django.contrib.auth.models import User
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass')
        user.save()
    
    # Login
    client.login(username='testuser', password='testpass')
    
    # URL de la vista registro
    url = reverse('registro')
    
    # Simular petición AJAX para cargar movimientos de ejercicio
    response = client.get(url, {
        'ejercicio_id': '1',  # Ejercicio 1 que debería existir
        'ajax': 'true',
        'get_ejercicio_movimientos': 'true'
    })
    
    print("=== RESPUESTA DE LA VISTA (EJERCICIO MOVIMIENTOS) ===")
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'No content-type')}")
    print(f"Content: {response.content.decode('utf-8')}")
    
    if response.status_code == 200:
        try:
            import json
            data = json.loads(response.content.decode('utf-8'))
            print("\n=== DATOS JSON ===")
            print(f"Success: {data.get('success', 'No success field')}")
            print(f"Movimientos: {len(data.get('movimientos', []))} movimientos encontrados")
            print(f"Resumen: {data.get('resumen', 'No resumen field')}")
            print(f"Ejercicio: {data.get('ejercicio', 'No ejercicio field')}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
    
    return response

if __name__ == "__main__":
    test_ajax_request()
