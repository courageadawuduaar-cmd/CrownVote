import requests
from django.conf import settings

PAYSTACK_SECRET = settings.PAYSTACK_SECRET_KEY
HEADERS = {
    'Authorization': f'Bearer {PAYSTACK_SECRET}',
    'Content-Type':  'application/json',
}


def initialize_payment(email, amount_ghs, reference, callback_url, metadata=None):
    """
    Initialize a Paystack transaction.
    amount_ghs: amount in Ghana Cedis (will be converted to pesewas)
    """
    amount_pesewas = int(amount_ghs * 100)
    payload = {
        'email':        email,
        'amount':       amount_pesewas,
        'reference':    reference,
        'callback_url': callback_url,
        'currency':     'GHS',
        'metadata':     metadata or {},
        'channels':     ['mobile_money'],
    }
    response = requests.post(
        'https://api.paystack.co/transaction/initialize',
        json=payload,
        headers=HEADERS,
        timeout=30,
    )
    return response.json()


def verify_payment(reference):
    """Verify a Paystack transaction by reference."""
    response = requests.get(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers=HEADERS,
        timeout=30,
    )
    return response.json()