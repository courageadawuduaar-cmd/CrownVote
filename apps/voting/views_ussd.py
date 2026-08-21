import uuid

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.nominees.models import Nominee
from apps.payments.models import Transaction
from apps.payments.utils.verifier import charge_mobile_money

# Paystack's mobile money provider codes, mapped from your Transaction.NETWORK_CHOICES
PROVIDER_MAP = {'mtn': 'mtn', 'telecel': 'vod', 'airtel': 'tgo'}
NETWORK_LABELS = {'1': 'mtn', '2': 'telecel', '3': 'airtel'}


def ussd(text):
    return HttpResponse(text, content_type='text/plain')


@csrf_exempt
def ussd_callback(request):
    phone = request.POST.get('msisdn', '').strip()
    user_input = request.POST.get('userInput', '').strip()
    steps = user_input.split('*') if user_input else []

    # Step 0: session just started
    if not steps or steps == ['']:
        return ussd('CON Welcome to NobleVote\nEnter nominee code:')

    # Step 1: nominee short_code entered
    if len(steps) == 1:
        code = steps[0].strip().upper()
        nominee = Nominee.objects.filter(short_code=code, is_active=True).first()
        if not nominee or not nominee.category.event.is_active:
            return ussd('END Invalid code or voting closed.')
        return ussd(
            f'CON Vote for {nominee.name}\n'
            f'{nominee.category.name} — {nominee.category.event.title}\n'
            f'Enter number of votes (₵1 each):'
        )

    # Step 2: quantity entered
    if len(steps) == 2:
        try:
            quantity = int(steps[1])
        except ValueError:
            return ussd('END Invalid number.')
        if quantity < 1:
            return ussd('END Please enter at least 1 vote.')
        return ussd(
            'CON Select network:\n'
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
            return ussd('END Invalid number.')
        network = NETWORK_LABELS.get(steps[2].strip())
        if not network:
            return ussd('END Invalid network selection.')

        nominee = Nominee.objects.filter(short_code=code, is_active=True).first()
        if not nominee:
            return ussd('END Nominee no longer available.')

        amount = quantity * 1  # ₵1 per vote, same as web flow
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
                f'END Approve the {network.upper()} prompt on your phone '
                f'to complete {quantity} vote(s) for {nominee.name}.'
            )
        else:
            return ussd('END Payment could not be started. Please try again.')

    return ussd('END Session ended.')