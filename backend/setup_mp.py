import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
USER_ID = os.getenv("MP_USER_ID")

print(f"Usando USER_ID: {USER_ID}")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def create_store():
    url = f"https://api.mercadopago.com/users/{USER_ID}/stores"
    payload = {
        "name": "Verduleria Central",
        "external_id": "ST001",
        "location": {
            "street_number": "123",
            "street_name": "Calle Falsa",
            "city_name": "Palermo",
            "state_name": "Capital Federal",
            "latitude": -34.6037,
            "longitude": -58.3816,
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        print("Sucursal creada con éxito.")
        return response.json()
    else:
        # Si ya existe, intentamos obtenerla o usar el external_id
        print(f"Info sucursal: {response.text}")
        if "already exists" in response.text.lower():
            # Intentamos obtener el ID real buscando por external_id no está directo en la API de creación, 
            # pero asumimos que si falla podemos seguir si tenemos el external_id para el POS
            # En modo prueba a veces es mejor simplemente reportar el error y ver si el POS se crea igual.
            pass
        return {"id": "ST_001_FALLBACK", "external_id": "ST_001"} # Fallback si ya existe

def create_pos():
    url = "https://api.mercadopago.com/pos"
    payload = {
        "name": "Caja 1",
        "fixed_amount": False,
        "external_store_id": "ST001",
        "external_id": "POS002",  # Changed to avoid conflict
        "category": 621102 
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        print("Caja creada con éxito.")
        return response.json()
    else:
        print(f"Error creando caja: {response.text}")
        return None

if __name__ == "__main__":
    create_store() # Intentamos crearla
    pos = create_pos()
    if pos:
        print("\n--- DATOS DE TU CAJA ---")
        print(f"POS ID (MP): {pos['id']}")
        print(f"External POS ID: {pos['external_id']}")
        print(f"QR URL: {pos['qr']['image']}")
        with open("mp_setup_result.json", "w") as f:
            json.dump(pos, f, indent=4)
    else:
        print("No se pudo obtener la información de la caja.")
