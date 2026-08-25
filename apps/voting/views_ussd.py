import json
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.nominees.models import Nominee
from apps.payments.models import Transaction
from apps.payments.utils.verifier import charge_mobile_money

# Paystack's mobile money provider codes, mapped from your Transaction.NETWORK_CHOICES
PROVIDER_MAP = {'mtn': 'mtn', 'telecel': 'vod', 'airtel': 'tgo'}
NETWORK_LABELS = {'1': 'mtn', '2': 'telecel', '3': 'airtel'}


def ussd(message, end=False):
    return JsonResponse({
        'continueSession': not end,
        'message': message,
    })


def _get_params(request):
    """Arkesel may send form-encoded or JSON — handle both."""
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return {}
    return request.POST


@csrf_exempt
def ussd_callback(request):
    params = _get_params(request)
    phone = (params.get('phoneNumber') or params.get('msisdn') or '').strip()
    user_input = params.get('text')
    if user_input is None:
        user_input = params.get('userInput', '')
    user_input = (user_input or '').strip()
    steps = user_input.split('*') if user_input else []

    # Step 0: session just started
    if not steps or steps == ['']:
        return ussd('Welcome to NobleVote\nEnter nominee code:')

    # Step 1: nominee short_code entered
    if len(steps) == 1:
        code = steps[0].strip().upper()
        nominee = Nominee.objects.filter(short_code=code, is_active=True).first()
        if not nominee or not nominee.category.event.is_active:
            return ussd('Invalid code or voting closed.', end=True)
        return ussd(
            f'Vote for {nominee.name}\n'
            f'{nominee.category.name} — {nominee.category.event.title}\n'
            f'Enter number of votes (₵{nominee.category.event.price_per_vote:g} each):'
        )

    # Step 2: quantity entered
    if len(steps) == 2:
        try:
            quantity = int(steps[1])
        except ValueError:
            return ussd('Invalid number.', end=True)
        if quantity < 1:
            return ussd('Please enter at least 1 vote.', end=True)
        return ussd(
            'Select network:\n'
            '1. MTN MoMo\n'
            '2. Telecel Cash\n'
            '3. AirtelTigo Money'
        )

    # Step 3: network chosen -> trigger charge
    if len(steps) == 3:
        code = steps[0].strip().upper()
        try:
            quantity = int(steps[1])
        except ValueError:
            return ussd('Invalid number.', end=True)
        network = NETWORK_LABELS.get(steps[2].strip())
        if not network:
            return ussd('Invalid network selection.', end=True)

        nominee = Nominee.objects.filter(short_code=code, is_active=True).first()
        if not nominee:
            return ussd('Nominee no longer available.', end=True)

        amount = quantity * nominee.category.event.price_per_vote
        reference = f'CV-USSD-{uuid.uuid4().hex[:10].upper()}'
        email = f'{phone}@crownvote.gh'

        Transaction.objects.create(
            nominee=nominee,
            reference=reference,
            phone_number=phone,
            network=network,
            amount=amount,
            vote_quantity=quantity,
            status='pending',
        )

        result = charge_mobile_money(
            email=email,
            amount_ghs=amount,
            reference=reference,
            phone_number=phone,
            provider=PROVIDER_MAP[network],
            metadata={
                'nominee_id': nominee.id,
                'vote_quantity': quantity,
                'source': 'ussd',
            },
        )

        if result.get('status'):
            return ussd(
                f'Approve the {network.upper()} prompt on your phone '
                f'to complete {quantity} vote(s) for {nominee.name}.',
                end=True,
            )
        else:
            return ussd('Payment could not be started. Please try again.', end=True)

    return ussd('Session ended.', end=True)