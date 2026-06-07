import uuid
import hmac
import hashlib
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction
from django.db.models import Sum

from apps.nominees.models import Nominee
from apps.payments.models import Transaction
from apps.payments.utils.verifier import initialize_payment, verify_payment
from apps.voting.models import Vote
from apps.voting.utils import encode_id, decode_id

QUICK_QUANTITIES = [5, 10, 20, 50, 100]


def vote(request, encoded_id):
    try:
        nominee_id = decode_id(encoded_id)
    except Exception:
        return HttpResponse('Invalid URL', status=404)

    nominee = get_object_or_404(Nominee, id=nominee_id, is_active=True)
    event   = nominee.category.event

    if not event.is_active:
        messages.error(request, 'Voting for this event is not currently active.')
        return redirect(f'/events/{event.slug}/')

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            messages.error(request, 'Invalid vote quantity.')
            return redirect(f'/voting/{encoded_id}/vote/')

        phone_number = request.POST.get('phone_number', '').strip()
        network      = request.POST.get('network_selected', 'mtn')
        voter_name   = request.POST.get('voter_name', '').strip()

        if quantity < 1:
            messages.error(request, 'Please select at least 1 vote.')
            return redirect(f'/voting/{encoded_id}/vote/')

        if len(phone_number) != 10 or not phone_number.isdigit():
            messages.error(request, 'Please enter a valid 10-digit phone number.')
            return redirect(f'/voting/{encoded_id}/vote/')

        amount    = quantity * 1  # ₵1 per vote
        reference = f'CV-{uuid.uuid4().hex[:12].upper()}'
        email     = f'{phone_number}@crownvote.gh'

        transaction = Transaction.objects.create(
            nominee       = nominee,
            reference     = reference,
            phone_number  = phone_number,
            network       = network,
            amount        = amount,
            vote_quantity = quantity,
            status        = 'pending',
        )

        callback_url = f"{settings.BASE_URL}/voting/verify/{reference}/"
        metadata     = {
            'nominee_id':    nominee.id,
            'nominee_name':  nominee.name,
            'vote_quantity': quantity,
            'voter_name':    voter_name,
            'phone':         phone_number,
        }

        result = initialize_payment(email, amount, reference, callback_url, metadata)

        if result.get('status') and result['data'].get('authorization_url'):
            request.session[f'paystack_url_{reference}'] = result['data']['authorization_url']
            return redirect(f'/voting/pending/{reference}/')
        else:
            transaction.status         = 'failed'
            transaction.failure_reason = str(result.get('message', 'Payment init failed'))
            transaction.save()
            messages.error(request, f"Payment could not be started: {result.get('message', 'Unknown error')}")
            return redirect(f'/voting/{encoded_id}/vote/')

    return render(request, 'voting/vote.html', {
        'nominee':          nominee,
        'encoded_id':       encoded_id,
        'quick_quantities': QUICK_QUANTITIES,
    })


def verify_vote(request, reference):
    transaction = get_object_or_404(Transaction, reference=reference)
    nominee     = transaction.nominee

    if transaction.status == 'success':
        return redirect(f'/voting/success/{reference}/')

    result = verify_payment(reference)

    if result.get('status') and result['data'].get('status') == 'success':
        with db_transaction.atomic():
            txn = Transaction.objects.select_for_update().get(reference=reference)

            if txn.status == 'success':
                return redirect(f'/voting/success/{reference}/')

            txn.status       = 'success'
            txn.verified_at  = timezone.now()
            txn.provider_ref = result['data'].get('id', '')
            txn.save()

            Vote.objects.create(
                nominee     = nominee,
                quantity    = txn.vote_quantity,
                amount_paid = txn.amount,
                ip_address  = request.META.get('REMOTE_ADDR'),
            )

        messages.success(request, f'✅ {txn.vote_quantity} vote(s) added for {nominee.name}!')
        return redirect(f'/voting/success/{reference}/')

    else:
        transaction.status         = 'failed'
        transaction.failure_reason = result['data'].get('gateway_response', 'Payment not completed')
        transaction.save()
        messages.error(request, '❌ Payment was not completed. Please try again.')
        encoded_id = encode_id(nominee.id)
        return redirect(f'/voting/{encoded_id}/vote/')


def payment_pending(request, reference):
    transaction  = get_object_or_404(Transaction, reference=reference)
    nominee      = transaction.nominee
    paystack_url = request.session.get(f'paystack_url_{reference}', '#')
    return render(request, 'voting/pending.html', {
        'transaction':  transaction,
        'nominee':      nominee,
        'paystack_url': paystack_url,
    })


def payment_status(request, reference):
    transaction = get_object_or_404(Transaction, reference=reference)

    if transaction.status == 'success':
        return JsonResponse({
            'status':       'success',
            'redirect_url': f'/voting/success/{reference}/'
        })

    if transaction.status == 'failed':
        encoded_id = encode_id(transaction.nominee.id)
        return JsonResponse({
            'status':       'failed',
            'redirect_url': f'/voting/{encoded_id}/vote/'
        })

    result = verify_payment(reference)

    if result.get('status') and result['data'].get('status') == 'success':
        with db_transaction.atomic():
            txn = Transaction.objects.select_for_update().get(reference=reference)

            if txn.status == 'success':
                return JsonResponse({
                    'status':       'success',
                    'redirect_url': f'/voting/success/{reference}/'
                })

            txn.status       = 'success'
            txn.verified_at  = timezone.now()
            txn.provider_ref = result['data'].get('id', '')
            txn.save()

            Vote.objects.create(
                nominee     = txn.nominee,
                quantity    = txn.vote_quantity,
                amount_paid = txn.amount,
                ip_address  = request.META.get('REMOTE_ADDR'),
            )

        return JsonResponse({
            'status':       'success',
            'redirect_url': f'/voting/success/{reference}/'
        })

    elif result['data'].get('status') == 'failed':
        transaction.status         = 'failed'
        transaction.failure_reason = result['data'].get('gateway_response', 'Payment failed')
        transaction.save()
        encoded_id = encode_id(transaction.nominee.id)
        return JsonResponse({
            'status':       'failed',
            'redirect_url': f'/voting/{encoded_id}/vote/'
        })

    return JsonResponse({'status': 'pending'})


def vote_success(request, reference):
    transaction = get_object_or_404(Transaction, reference=reference, status='success')
    nominee     = transaction.nominee
    encoded_id  = encode_id(nominee.id)
    return render(request, 'voting/success.html', {
        'transaction': transaction,
        'nominee':     nominee,
        'encoded_id':  encoded_id,
    })


def campaign(request, slug, encoded_id):
    try:
        nominee_id = decode_id(encoded_id)
    except Exception:
        return HttpResponse('Invalid URL', status=404)

    nominee   = get_object_or_404(Nominee, id=nominee_id, slug=slug, is_active=True)
    event     = nominee.category.event
    category  = nominee.category

    base_url     = request.build_absolute_uri('/')[:-1]
    campaign_url = f"{base_url}/voting/campaign/{nominee.slug}-{encode_id(nominee.id)}/"

    # Build absolute OG image URL for WhatsApp/Facebook scrapers
    if nominee.photo:
        og_image_url = nominee.photo.url
        # Cloudinary returns absolute HTTPS URLs — ensure no protocol-relative slashes
        if og_image_url.startswith('//'):
            og_image_url = 'https:' + og_image_url
    else:
        og_image_url = f"{base_url}/static/images/crownvote.png"

    whatsapp_msg = (
        f"🗳 Vote for *{nominee.name}* in the *{event.title}*!\n\n"
        f"Category: {category.name}\n"
        f"Current votes: {nominee.total_votes}\n\n"
        f"Click the link below to vote now 👇\n"
        f"₵1 = 1 Vote | Pay via MoMo\n\n"
        f"{campaign_url}"
    )

    other_nominees = category.nominees.filter(
        is_active=True
    ).exclude(id=nominee.id).annotate(
        total=Sum('votes__quantity')
    ).order_by('-total')[:4]

    return render(request, 'voting/campaign.html', {
        'nominee':          nominee,
        'event':            event,
        'category':         category,
        'campaign_url':     campaign_url,
        'og_image_url':     og_image_url,
        'whatsapp_msg':     whatsapp_msg,
        'other_nominees':   other_nominees,
        'quick_quantities': QUICK_QUANTITIES,
        'encoded_id':       encode_id(nominee.id),
    })


@csrf_exempt
def paystack_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    paystack_signature = request.headers.get('x-paystack-signature', '')
    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        request.body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(paystack_signature, expected_signature):
        return HttpResponse('Invalid signature', status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse('Invalid payload', status=400)

    if payload.get('event') == 'charge.success':
        data      = payload['data']
        reference = data.get('reference')

        try:
            with db_transaction.atomic():
                txn = Transaction.objects.select_for_update().get(reference=reference)

                if txn.status == 'success':
                    return HttpResponse(status=200)

                txn.status       = 'success'
                txn.verified_at  = timezone.now()
                txn.provider_ref = str(data.get('id', ''))
                txn.save()

                Vote.objects.create(
                    nominee     = txn.nominee,
                    quantity    = txn.vote_quantity,
                    amount_paid = txn.amount,
                )

        except Transaction.DoesNotExist:
            pass

    return HttpResponse(status=200)