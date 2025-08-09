from django.shortcuts import render
from django.http import JsonResponse
from .models import MovimientoCajaIngreso, MovimientoCajaGasto, MovimientoCajaDeposito, MovimientoCajaRetirada, MovimientoCajaTransferencia
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from apps.dyn_dt.models import Ejercicio, Campamento
from apps.caja.models import Caja
from django.db.models import Q


#  AJAX functions for Caja app


def get_movimientos_caja_ingresos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        campamento_id = request.GET.get("campamento_id")
        caja_id = request.GET.get("caja_id")
        order_by = request.GET.get("order_by") or "-fecha"

        filtros = Q()
        if ejercicio_id:
            filtros &= Q(ejercicio_id=ejercicio_id)
        if campamento_id:
            filtros &= Q(caja__campamento_id=campamento_id)
        if caja_id:
            filtros &= Q(caja_id=caja_id)

        movimientos = MovimientoCajaIngreso.objects.filter(filtros).order_by(order_by)

        data = []
        for m in movimientos:
            data.append(m.serializar())
        return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Invalid request"}, status=400)


def get_movimientos_caja_gastos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        campamento_id = request.GET.get("campamento_id")
        caja_id = request.GET.get("caja_id")
        order_by = request.GET.get("order_by") or "-fecha"

        filtros = Q()
        if ejercicio_id:
            filtros &= Q(ejercicio_id=ejercicio_id)
        if campamento_id:
            filtros &= Q(caja__campamento_id=campamento_id)
        if caja_id:
            filtros &= Q(caja_id=caja_id)

        movimientos = MovimientoCajaGasto.objects.filter(filtros).order_by(order_by)

        data = []
        for m in movimientos:
            data.append(m.serializar())
        return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Invalid request"}, status=400)



def get_movimientos_caja_depositos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        campamento_id = request.GET.get("campamento_id")
        caja_id = request.GET.get("caja_id")
        order_by = request.GET.get("order_by") or "-fecha"

        movimientos = MovimientoCajaDeposito.objects.all()

        if ejercicio_id:
            ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
            movimientos = movimientos.filter(ejercicio=ejercicio)

        if campamento_id:
            movimientos = movimientos.filter(caja__campamento__id=campamento_id)

        if caja_id:
            movimientos = movimientos.filter(caja__id=caja_id)

        movimientos = movimientos.order_by(order_by)

        data = []
        for movimiento in movimientos:
            data.append(movimiento.serializar())
        return JsonResponse(data, safe=False)

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_movimientos_caja_retiradas(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        campamento_id = request.GET.get("campamento_id")
        caja_id = request.GET.get("caja_id")
        order_by = request.GET.get("order_by") or "-fecha"

        movimientos = MovimientoCajaRetirada.objects.all()

        if ejercicio_id:
            ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
            movimientos = movimientos.filter(ejercicio=ejercicio)

        if campamento_id:
            movimientos = movimientos.filter(caja__campamento__id=campamento_id)

        if caja_id:
            movimientos = movimientos.filter(caja__id=caja_id)

        movimientos = movimientos.order_by(order_by)

        data = []
        for movimiento in movimientos:
            data.append(movimiento.serializar())
        return JsonResponse(data, safe=False)

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_movimientos_caja_transferencias(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        ejercicio_id = request.GET.get("ejercicio_id")
        caja_origen_id = request.GET.get("caja_id")
        caja_destino_id = request.GET.get("caja_destino_id")
        order_by = request.GET.get("order_by") or "-fecha"

        filtros = Q()
        if ejercicio_id:
            filtros &= Q(ejercicio_id=ejercicio_id)
        if caja_origen_id:
            filtros &= Q(caja_origen_id=caja_origen_id)
        if caja_destino_id:
            filtros &= Q(caja_destino_id=caja_destino_id)

        movimientos = MovimientoCajaTransferencia.objects.filter(filtros).order_by(order_by)

        data = []
        for movimiento in movimientos:
            data.append(movimiento.serializar())
        return JsonResponse(data, safe=False)

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_movimientos_caja_ingresos_data(request):
    """Helper function that returns raw data instead of JsonResponse"""
    ejercicio_id = request.GET.get("ejercicio_id")
    campamento_id = request.GET.get("campamento_id")
    caja_id = request.GET.get("caja_id")
    order_by = request.GET.get("order_by") or "-fecha"

    filtros = Q()
    if ejercicio_id:
        filtros &= Q(ejercicio_id=ejercicio_id)
    if campamento_id:
        filtros &= Q(caja__campamento_id=campamento_id)
    if caja_id:
        filtros &= Q(caja_id=caja_id)

    movimientos = MovimientoCajaIngreso.objects.filter(filtros).order_by(order_by)
    return [m.serializar() for m in movimientos]


def get_movimientos_caja_gastos_data(request):
    """Helper function that returns raw data instead of JsonResponse"""
    ejercicio_id = request.GET.get("ejercicio_id")
    campamento_id = request.GET.get("campamento_id")
    caja_id = request.GET.get("caja_id")
    order_by = request.GET.get("order_by") or "-fecha"

    filtros = Q()
    if ejercicio_id:
        filtros &= Q(ejercicio_id=ejercicio_id)
    if campamento_id:
        filtros &= Q(caja__campamento_id=campamento_id)
    if caja_id:
        filtros &= Q(caja_id=caja_id)

    movimientos = MovimientoCajaGasto.objects.filter(filtros).order_by(order_by)
    return [m.serializar() for m in movimientos]


def get_movimientos_caja_depositos_data(request):
    """Helper function that returns raw data instead of JsonResponse"""
    ejercicio_id = request.GET.get("ejercicio_id")
    campamento_id = request.GET.get("campamento_id")
    caja_id = request.GET.get("caja_id")
    order_by = request.GET.get("order_by") or "-fecha"

    movimientos = MovimientoCajaDeposito.objects.all()

    if ejercicio_id:
        ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
        movimientos = movimientos.filter(ejercicio=ejercicio)
    if campamento_id:
        movimientos = movimientos.filter(caja__campamento__id=campamento_id)
    if caja_id:
        movimientos = movimientos.filter(caja__id=caja_id)

    movimientos = movimientos.order_by(order_by)
    return [m.serializar() for m in movimientos]


def get_movimientos_caja_retiradas_data(request):
    """Helper function that returns raw data instead of JsonResponse"""
    ejercicio_id = request.GET.get("ejercicio_id")
    campamento_id = request.GET.get("campamento_id")
    caja_id = request.GET.get("caja_id")
    order_by = request.GET.get("order_by") or "-fecha"

    movimientos = MovimientoCajaRetirada.objects.all()

    if ejercicio_id:
        ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
        movimientos = movimientos.filter(ejercicio=ejercicio)
    if campamento_id:
        movimientos = movimientos.filter(caja__campamento__id=campamento_id)
    if caja_id:
        movimientos = movimientos.filter(caja__id=caja_id)

    movimientos = movimientos.order_by(order_by)
    return [m.serializar() for m in movimientos]


def get_movimientos_caja_transferencias_data(request):
    """Helper function that returns raw data instead of JsonResponse"""
    ejercicio_id = request.GET.get("ejercicio_id")
    caja_origen_id = request.GET.get("caja_id")
    caja_destino_id = request.GET.get("caja_destino_id")
    order_by = request.GET.get("order_by") or "-fecha"

    filtros = Q()
    if ejercicio_id:
        filtros &= Q(ejercicio_id=ejercicio_id)
    if caja_origen_id:
        filtros &= Q(caja_origen_id=caja_origen_id)
    if caja_destino_id:
        filtros &= Q(caja_destino_id=caja_destino_id)

    movimientos = MovimientoCajaTransferencia.objects.filter(filtros).order_by(order_by)
    return [m.serializar() for m in movimientos]


