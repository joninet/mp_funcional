import os
import requests
import json
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class CreateOrderView(APIView):
    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response({"error": "Monto es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        # Usamos el external_pos_id y external_store_id que creamos en el setup
        external_pos_id = "POS002" 
        external_store_id = "ST001"
        
        # Endpoint para QR Fijo (v2) - Modelo Atendido
        # https://api.mercadopago.com/instore/qr/seller/collectors/{user_id}/stores/{external_store_id}/pos/{external_pos_id}/orders
        url = f"https://api.mercadopago.com/instore/qr/seller/collectors/{settings.MP_USER_ID}/stores/{external_store_id}/pos/{external_pos_id}/orders"
        
        headers = {
            "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        order_data = {
            "external_reference": str(uuid.uuid4()),
            "title": "Venta de Verduleria",
            "total_amount": float(amount),
            "items": [
                {
                    "title": "Productos varios",
                    "unit_price": float(amount),
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": float(amount)
                }
            ],
            "description": "Venta de Verduleria"
        }

        # En QR Fijo v2 se usa PUT
        response = requests.put(url, headers=headers, json=order_data)
        
        if response.status_code in [200, 201, 204]:
            return Response({
                "status": "success",
                "message": "Monto cargado al QR fijo",
                "external_reference": order_data['external_reference']
            }, status=status.HTTP_200_OK)
        else:
            print(f"Error de MercadoPago: {response.status_code} - {response.text}")
            return Response({
                "error": "No se pudo cargar el monto al QR",
                "details": response.json() if response.text else "Respuesta vacía"
            }, status=response.status_code)

class GetQRInfoView(APIView):
    def get(self, request):
        # En una app real esto vendría de la DB. Aquí lo leemos del archivo de setup o lo hardcodeamos
        setup_file = os.path.join(settings.BASE_DIR, 'mp_setup_result.json')
        if os.path.exists(setup_file):
            with open(setup_file, 'r') as f:
                data = json.load(f)
                return Response({
                    "qr_image": data['qr']['image'],
                    "external_pos_id": data['external_id']
                })
        return Response({"error": "No se encontró configuración de caja. Corre setup_mp.py primero."}, status=404)

class WebhookView(APIView):
    def post(self, request):
        # Mercado Pago envía notificaciones aquí
        print("WEBHOOK RECEIVED:", request.data)
        # Aquí deberías validar el pago consultando la API de MP con el ID recibido
        return Response(status=status.HTTP_200_OK)

class CheckOrderStatusView(APIView):
    def get(self, request, order_id):
        # Para órdenes in-store, buscar payments relacionados
        url = f"https://api.mercadopago.com/v1/payments/search?external_reference={order_id}"
        
        headers = {
            "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                payment = data['results'][0]  # Tomar el primer pago
                status = payment.get('status', 'unknown')
                return Response({
                    'status': status,
                    'payment_data': payment
                })
            else:
                # Si no hay payments, la orden aún no fue pagada
                return Response({
                    'status': 'pending',
                    'message': 'Orden creada, esperando pago'
                })
        else:
            return Response({
                'error': 'No se pudo consultar el estado del pago',
                'details': response.json() if response.text else 'Error desconocido'
            }, status=response.status_code)
