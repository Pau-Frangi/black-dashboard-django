from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from apps.dyn_dt.models import Ejercicio, Campamento
from apps.banco.models import MovimientoBancoIngreso, MovimientoBancoGasto
from django.db.models import Q



def get_movimientos_banco_ingreso(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        campamento_id = request.GET.get("campamento_id")
        cuenta_bancaria_id = request.GET.get("cuenta_bancaria_id")
        order_by = request.GET.get("order_by") or "-fecha"

        filtros = Q()
        if ejercicio_id:
            filtros &= Q(ejercicio_id=ejercicio_id)
        if campamento_id:
            filtros &= Q(campamento_id=campamento_id)
        if cuenta_bancaria_id:
            filtros &= Q(cuenta_bancaria_id=cuenta_bancaria_id)

        movimientos = MovimientoBancoIngreso.objects.filter(filtros).order_by(order_by)

        data = []
        for m in movimientos:
            data.append(m.serializar())
        return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Invalid request"}, status=400)


def get_movimientos_banco_gasto(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        campamento_id = request.GET.get("campamento_id")
        cuenta_bancaria_id = request.GET.get("cuenta_bancaria_id")
        order_by = request.GET.get("order_by") or "-fecha"

        filtros = Q()
        if ejercicio_id:
            filtros &= Q(ejercicio_id=ejercicio_id)
        if campamento_id:
            filtros &= Q(campamento_id=campamento_id)
        if cuenta_bancaria_id:
            filtros &= Q(cuenta_bancaria_id=cuenta_bancaria_id)

        movimientos = MovimientoBancoGasto.objects.filter(filtros).order_by(order_by)

        data = []
        for m in movimientos:
            data.append(m.serializar())
        return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Invalid request"}, status=400)