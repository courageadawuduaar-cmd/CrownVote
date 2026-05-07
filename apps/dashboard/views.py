from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from apps.events.models import Event
from apps.nominees.models import Nominee
from apps.payments.models import Transaction
from apps.voting.models import Vote

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak
)


NAV_ITEMS = [
    {'icon': '📊', 'label': 'Dashboard',    'url': '/dashboard/'},
    {'icon': '🎉', 'label': 'Events',       'url': '/admin/events/event/'},
    {'icon': '🏷️', 'label': 'Categories',   'url': '/admin/categories/category/'},
    {'icon': '👤', 'label': 'Nominees',     'url': '/admin/nominees/nominee/'},
    {'icon': '💳', 'label': 'Transactions', 'url': '/admin/payments/transaction/'},
    {'icon': '🗳',  'label': 'Votes',        'url': '/admin/voting/vote/'},
    {'icon': '📈', 'label': 'Live Results', 'url': '/results/'},
]


@login_required(login_url='/accounts/login/')
def dashboard(request):
    user = request.user

    if user.is_staff or user.is_superuser:
        return superadmin_dashboard(request)

    events = Event.objects.filter(organizer=user)
    if not events.exists():
        return render(request, 'dashboard/no_event.html')

    return organizer_dashboard(request, events)


def superadmin_dashboard(request):
    total_votes         = Vote.objects.aggregate(t=Sum('quantity'))['t'] or 0
    total_revenue       = Transaction.objects.filter(status='success').aggregate(t=Sum('amount'))['t'] or 0
    active_events       = Event.objects.filter(status='active').count()
    total_nominees      = Nominee.objects.filter(is_active=True).count()
    events              = Event.objects.exclude(status='draft').order_by('-created_at')
    top_nominees        = sorted(
                            Nominee.objects.filter(is_active=True),
                            key=lambda n: n.total_votes, reverse=True
                          )[:8]
    recent_transactions = Transaction.objects.select_related('nominee').order_by('-created_at')[:10]

    return render(request, 'dashboard/dashboard.html', {
        'total_votes':          total_votes,
        'total_revenue':        total_revenue,
        'active_events':        active_events,
        'total_nominees':       total_nominees,
        'events':               events,
        'top_nominees':         top_nominees,
        'recent_transactions':  recent_transactions,
        'nav_items':            NAV_ITEMS,
        'is_superadmin':        True,
    })


def organizer_dashboard(request, events):
    from apps.payments.models import Transaction
    from apps.nominees.models import Nominee

    # Build per-event data
    event_data = []
    grand_total_votes    = 0
    grand_total_revenue  = Decimal(0)
    grand_commission     = Decimal(0)
    grand_net            = Decimal(0)

    for event in events:
        categories = event.categories.filter(is_active=True)
        votes      = event.total_votes
        revenue    = event.total_revenue
        commission = event.commission_amount
        net        = event.net_revenue

        grand_total_votes   += votes
        grand_total_revenue += revenue
        grand_commission    += commission
        grand_net           += net

        recent_txns = Transaction.objects.filter(
            nominee__category__event=event,
            status='success'
        ).select_related('nominee').order_by('-created_at')[:5]

        top_nominees = sorted(
            Nominee.objects.filter(category__event=event, is_active=True),
            key=lambda n: n.total_votes, reverse=True
        )[:5]

        event_data.append({
            'event':               event,
            'categories':          categories,
            'total_votes':         votes,
            'total_revenue':       revenue,
            'commission_rate':     event.commission_rate,
            'commission_amount':   commission,
            'net_revenue':         net,
            'recent_transactions': recent_txns,
            'top_nominees':        top_nominees,
        })

    return render(request, 'dashboard/organizer_dashboard.html', {
        'event_data':         event_data,
        'grand_total_votes':  grand_total_votes,
        'grand_total_revenue': grand_total_revenue,
        'grand_commission':   grand_commission,
        'grand_net':          grand_net,
        'multiple_events':    events.count() > 1,
    })


@login_required(login_url='/accounts/login/')
def organizer_list(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponse('Unauthorized', status=403)

    from django.contrib.auth.models import User
    organizers = User.objects.filter(
        events__isnull=False
    ).distinct().prefetch_related('events')

    organizer_data = []
    for org in organizers:
        events      = org.events.all()
        total_votes = sum(e.total_votes for e in events)
        total_gross = sum(e.total_revenue for e in events)
        total_net   = sum(e.net_revenue for e in events)
        organizer_data.append({
            'user':         org,
            'events':       events,
            'event_count':  events.count(),
            'total_votes':  total_votes,
            'total_gross':  total_gross,
            'total_net':    total_net,
        })

    return render(request, 'dashboard/dashboard.html', {
        'organizer_data':   organizer_data,
        'active_tab':       'organizers',
        'nav_items':        NAV_ITEMS,
        'is_superadmin':    True,
        # Pass these so the template doesn't break on other tab stats
        'total_votes':      Vote.objects.aggregate(t=Sum('quantity'))['t'] or 0,
        'total_revenue':    Transaction.objects.filter(status='success').aggregate(t=Sum('amount'))['t'] or 0,
        'active_events':    Event.objects.filter(status='active').count(),
        'total_nominees':   Nominee.objects.filter(is_active=True).count(),
        'events':           Event.objects.exclude(status='draft').order_by('-created_at'),
        'top_nominees':     [],
        'recent_transactions': Transaction.objects.select_related('nominee').order_by('-created_at')[:10],
    })


@login_required(login_url='/accounts/login/')
def organizer_detail(request, user_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponse('Unauthorized', status=403)

    from django.contrib.auth.models import User
    organizer = get_object_or_404(User, id=user_id)
    events    = Event.objects.filter(organizer=organizer)

    event_data = []
    for event in events:
        event_data.append({
            'event':             event,
            'total_votes':       event.total_votes,
            'total_revenue':     event.total_revenue,
            'commission_rate':   event.commission_rate,
            'commission_amount': event.commission_amount,
            'net_revenue':       event.net_revenue,
            'categories':        event.categories.filter(is_active=True),
            'recent_transactions': Transaction.objects.filter(
                                     nominee__category__event=event,
                                     status='success'
                                   ).select_related('nominee').order_by('-created_at')[:10],
        })

    total_gross = sum(e['total_revenue'] for e in event_data)
    total_net   = sum(e['net_revenue'] for e in event_data)
    total_votes = sum(e['total_votes'] for e in event_data)

    return render(request, 'dashboard/organizer_detail.html', {
        'organizer':   organizer,
        'event_data':  event_data,
        'total_gross': total_gross,
        'total_net':   total_net,
        'total_votes': total_votes,
        'nav_items':   NAV_ITEMS,
    })

@login_required(login_url='/accounts/login/')
def download_report(request, slug):
    import os

    event = get_object_or_404(Event, slug=slug)

    if not request.user.is_staff and not request.user.is_superuser:
        if event.organizer != request.user:
            return HttpResponse('Unauthorized', status=403)

    # ── Data ────────────────────────────────────────────
    categories        = event.categories.filter(is_active=True)
    total_votes       = event.total_votes
    total_revenue     = event.total_revenue
    commission_rate   = event.commission_rate
    commission_amount = event.commission_amount
    net_revenue       = event.net_revenue
    generated_on      = timezone.now().strftime('%B %d, %Y at %H:%M')
    organizer_name    = (
        event.organizer.get_full_name() or event.organizer.username
        if event.organizer else 'N/A'
    )

    # ── Colors ──────────────────────────────────────────
    RED        = colors.HexColor('#C8102E')
    GOLD       = colors.HexColor('#D4AF37')
    ASH        = colors.HexColor('#2C2C2C')
    LIGHT_GOLD = colors.HexColor('#FDF6E3')
    LIGHT_GREY = colors.HexColor('#F5F5F5')
    WHITE      = colors.white

    # ── PDF Setup ───────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="{event.slug}_report.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=60,
    )

    elements = []
    styles   = getSampleStyleSheet()

    # ── Custom Styles ────────────────────────────────────
    brand_name_style = ParagraphStyle(
        'BrandName', parent=styles['Normal'],
        fontSize=28, fontName='Helvetica-Bold',
        textColor=ASH, alignment=1, spaceAfter=2,
    )
    tagline_style = ParagraphStyle(
        'Tagline', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica',
        textColor=colors.HexColor('#888888'),
        alignment=1, spaceAfter=2,
    )
    report_title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Normal'],
        fontSize=12, fontName='Helvetica-Bold',
        textColor=GOLD, alignment=1, spaceAfter=4,
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold',
        textColor=WHITE, leftIndent=8,
    )
    normal = styles['Normal']

    # ── LOGO + HEADER BLOCK ──────────────────────────────
    from reportlab.platypus import Image as RLImage

    logo_path = os.path.join(
        str(doc.topMargin),  # placeholder — overridden below
    )
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..', 'static', 'images', 'crownvote.png'
    )
    logo_path = os.path.normpath(logo_path)

    # Header table: logo left, brand name + tagline center, empty right
    if os.path.exists(logo_path):
        from reportlab.platypus import Flowable

        class RoundedImage(Flowable):
            def __init__(self, path, width, height, radius=10):
                self.path   = path
                self.iwidth  = width
                self.iheight = height
                self.radius = radius
                self.width  = width
                self.height = height

            def draw(self):
                self.canv.saveState()
                p = self.canv.beginPath()
                p.roundRect(0, 0, self.iwidth, self.iheight, self.radius)
                self.canv.clipPath(p, stroke=0, fill=0)
                self.canv.drawImage(
                    self.path, 0, 0,
                    width=self.iwidth, height=self.iheight,
                    preserveAspectRatio=True, mask='auto'
                )
                self.canv.restoreState()

        logo = RoundedImage(logo_path, width=75, height=75, radius=12)
    else:
        logo = Paragraph('', normal)

    header_left  = logo
    header_mid = [
        Paragraph('<b>CrownVote</b>', brand_name_style),
        Spacer(1, 12),
        Paragraph('Official Event Financial Report', report_title_style),
    ]
    header_right = Paragraph('', normal)

    # Stack the middle paragraphs in a sub-table
    mid_table = Table(
        [[p] for p in header_mid],
        colWidths=[4.0*inch],
        rowHeights=[40, 12, 20]
    )
    mid_table.setStyle(TableStyle([
        ('ALIGN',          (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',         (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',        (0,0), (-1,-1), 2),
        ('LINEBELOW',      (0,0), (-1,0),  0.5, colors.HexColor('#dddddd')),
    ]))

    header_table = Table(
        [[header_left, mid_table, header_right]],
        colWidths=[1.0*inch, 4.3*inch, 1.0*inch]
    )
    header_table.setStyle(TableStyle([
        ('ALIGN',  (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # Gold + ash divider
    divider = Table([['']], colWidths=[6.3*inch])
    divider.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 0.5, ASH),
        ('LINEBELOW', (0,0), (-1,-1), 3,   GOLD),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 16))

    # ── Event Info ───────────────────────────────────────
    info_data = [
        [Paragraph('<b>Event:</b>', normal),     Paragraph(event.title, normal)],
        [Paragraph('<b>Organizer:</b>', normal), Paragraph(organizer_name, normal)],
        [Paragraph('<b>Status:</b>', normal),    Paragraph(event.get_status_display(), normal)],
        [Paragraph('<b>Period:</b>', normal),    Paragraph(
            f"{event.start_date.strftime('%b %d, %Y')} — {event.end_date.strftime('%b %d, %Y')}",
            normal
        )],
        [Paragraph('<b>Generated:</b>', normal), Paragraph(generated_on, normal)],
    ]
    info_table = Table(info_data, colWidths=[1.8*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # ── Financial Summary ────────────────────────────────
    fin_header = Table(
        [[Paragraph('FINANCIAL SUMMARY', section_style)]],
        colWidths=[6.3*inch]
    )
    fin_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), ASH),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW',     (0,0), (-1,-1), 2, GOLD),
    ]))
    elements.append(fin_header)

    fin_data = [
        ['Total Votes Cast',                str(total_votes)],
        ['Gross Revenue (GHS)',              f'GHS {total_revenue}'],
        [f'Commission ({commission_rate}%)', f'- GHS {commission_amount}'],
        ['Net Earnings (GHS)',               f'GHS {net_revenue}'],
    ]
    fin_table = Table(fin_data, colWidths=[4.5*inch, 1.8*inch])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), LIGHT_GOLD),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [WHITE, LIGHT_GOLD]),
        ('BOX',           (0,0), (-1,-1), 0.5, ASH),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ALIGN',         (1,0), (-1,-1), 'RIGHT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME',      (0,0), (0,-1),  'Helvetica-Bold'),
        ('FONTNAME',      (1,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING',   (0,0), (0,-1),  12),
        ('RIGHTPADDING',  (1,0), (-1,-1), 12),
        # Net earnings row — green
        ('BACKGROUND',    (0,3), (-1,3), colors.HexColor('#E8F5E9')),
        ('TEXTCOLOR',     (1,3), (1,3),  colors.HexColor('#1B5E20')),
        # Commission row — red
        ('TEXTCOLOR',     (1,2), (1,2),  RED),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 28))

    # ── Category Breakdown ───────────────────────────────
    cat_header = Table(
        [[Paragraph('CATEGORY BREAKDOWN', section_style)]],
        colWidths=[6.3*inch]
    )
    cat_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), ASH),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW',     (0,0), (-1,-1), 2, GOLD),
    ]))
    elements.append(cat_header)

    cat_data = [[
        Paragraph('<b>Category</b>', normal),
        Paragraph('<b>Votes</b>', normal),
        Paragraph('<b>Revenue (GHS)</b>', normal),
        Paragraph('<b>% of Total</b>', normal),
    ]]
    for cat in categories:
        cat_votes   = cat.total_votes
        cat_revenue = Decimal(cat_votes)
        cat_pct     = round((cat_votes / total_votes * 100), 1) if total_votes > 0 else 0
        cat_data.append([
            cat.name,
            str(cat_votes),
            f'GHS {cat_revenue}',
            f'{cat_pct}%',
        ])

    cat_table = Table(cat_data, colWidths=[3.0*inch, 1.0*inch, 1.5*inch, 0.8*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), ASH),
        ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ('BOX',           (0,0), (-1,-1), 0.5, ASH),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (0,1), (0,-1),  10),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 28))

    # ── Nominee Leaderboard ──────────────────────────────
    nom_header = Table(
        [[Paragraph('NOMINEE LEADERBOARD', section_style)]],
        colWidths=[6.3*inch]
    )
    nom_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), ASH),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW',     (0,0), (-1,-1), 2, GOLD),
    ]))
    elements.append(nom_header)

    nom_data = [[
        Paragraph('<b>Rank</b>', normal),
        Paragraph('<b>Nominee</b>', normal),
        Paragraph('<b>Category</b>', normal),
        Paragraph('<b>Votes</b>', normal),
        Paragraph('<b>%</b>', normal),
    ]]

    all_nominees = sorted(
        Nominee.objects.filter(category__event=event, is_active=True),
        key=lambda n: n.total_votes, reverse=True
    )

    for rank, nominee in enumerate(all_nominees, start=1):
        is_winner = rank == 1
        nom_data.append([
            Paragraph(f'<b>{rank}</b>', normal),
            Paragraph(f'<b>{nominee.name}</b>' if is_winner else nominee.name, normal),
            nominee.category.name,
            str(nominee.total_votes),
            f'{nominee.vote_percentage}%',
        ])

    nom_table = Table(
        nom_data,
        colWidths=[0.5*inch, 2.3*inch, 1.8*inch, 0.9*inch, 0.8*inch]
    )
    nom_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), ASH),
        ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ('BACKGROUND',    (0,1), (-1,1), LIGHT_GOLD),
        ('BOX',           (0,0), (-1,-1), 0.5, ASH),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('ALIGN',         (0,0), (0,-1), 'CENTER'),
        ('ALIGN',         (3,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (1,1), (1,-1), 8),
    ]))
    elements.append(nom_table)
    elements.append(Spacer(1, 28))

    # ── Watermark & Border ───────────────────────────────
    def add_watermark(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setLineWidth(3)
        canvas_obj.setStrokeColor(ASH)
        canvas_obj.rect(20, 20, A4[0]-40, A4[1]-40)
        canvas_obj.setLineWidth(1)
        canvas_obj.setStrokeColor(GOLD)
        canvas_obj.rect(26, 26, A4[0]-52, A4[1]-52)
        canvas_obj.setFont('Helvetica-Bold', 60)
        canvas_obj.setFillColor(ASH)
        canvas_obj.setFillAlpha(0.04)
        canvas_obj.translate(A4[0]/2, A4[1]/2)
        canvas_obj.rotate(45)
        canvas_obj.drawCentredString(0, 0, 'CROWNVOTE')
        canvas_obj.rotate(-45)
        canvas_obj.translate(-A4[0]/2, -A4[1]/2)
        canvas_obj.restoreState()
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#888888'))
        canvas_obj.drawCentredString(
            A4[0]/2, 12,
            f'CrownVote Financial Report  |  {event.title}  |  Page {doc.page}'
        )

    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
    return response