# -*- coding: utf-8 -*-
"""Define the Grant views.

Copyright (C) 2018 Gitcoin Core

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
import json
import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from grants.models import Grant, Subscription
from marketing.models import Keyword
from web3 import HTTPProvider, Web3

logger = logging.getLogger(__name__)
w3 = Web3(HTTPProvider(settings.WEB3_HTTP_PROVIDER))


def get_keywords():
    """Get all Keywords."""
    return json.dumps([str(key) for key in Keyword.objects.all().values_list('keyword', flat=True)])


def grants(request):
    """Handle grants explorer."""
    grants = Grant.objects.all()

    params = {
        'active': 'dashboard',
        'title': _('Grants Explorer'),
        'grants': grants,
        'keywords': get_keywords(),
    }
    return TemplateResponse(request, 'grants/index.html', params)


def grant_details(request, grant_id):
    """Display the Grant details page."""
    profile = request.user.profile if request.user.is_authenticated else None

    try:
        grant = Grant.objects.prefetch_related('subscriptions').get(pk=grant_id)
    except Grant.DoesNotExist:
        raise Http404

    # TODO: Determine how we want to chunk out articles and where we want to store this data.
    activity_data = [{
        'title': 'allow funder to turn off auto approvals during bounty creation',
        'date': '08.02.2018',
        'description':
            'Vestibulum ante ipsum primis in faucibus orci luctus ultrices '
            'posuere cubilia Curae; Proin vel ante.',
    }, {
        'title': 'Beyond The Naked Eye',
        'date': '2012 - Present',
        'description':
            'What is the loop of Creation? How is there something from nothing? '
            'In spite of the fact that it is impossible to prove that anything exists beyond '
            'one’s perception since any such proof would involve one’s perception (I observed it, '
            'I heard it, I thought about it, I calculated it, and etc.), science deals with a '
            'so-called objective reality “out there,” beyond one’s perception professing to '
            'describe Nature objectively (as if there was a Nature or reality external '
            'to one’s perception). The shocking impact of Matrix was precisely the valid '
            'possibility that what we believed to be reality was but our perception; however, '
            'this was presented through showing a real reality wherein the perceived reality was a '
            'computer simulation. Many who toy with the idea that perhaps, indeed, we are computer '
            'simulations, deviate towards questions, such as, who could create such software and what '
            'kind of hardware would be needed for such a feat. Although such questions assume that reality '
            'is our perception, they also axiomatically presuppose the existence of an objective '
            'deterministic world “out there” that nevertheless must be responsible for how we perceive '
            'our reality. This is a major mistake emphasizing technology and algorithms instead of trying '
            'to discover the nature of reality and the structure of creation. As will be shown in the following, '
            'the required paradigm shift from “perception is our reality fixed within an objective world,” '
            'to “perception is reality without the need of an objective world ‘out there,” '
            'is provided by a dynamic logical structure. The Holophanic loop logic is responsible '
            'for a consistent and complete worldview that not only describes, but also creates whatever '
            'can be perceived or experienced.'
    }, {
        'title': 'Awesome Update',
        'date': '08.02.2018',
        'description': 'Some awesome update about this project.',
    }, {
        'title': 'Stellar Update',
        'date': '08.02.2018',
        'description': 'Another stellar update about this project.',
    }]

    gh_data = [{
        'title': 'Initial commit by flapjacks',
        'date': '08.02.2018',
        'description': 'Initial commit with some blah blah blah...',
    }, {
        'title': 'Fix the build by derp-nation',
        'date': '08.02.2018',
        'description': 'Initial commit with some blah blah blah...',
    }, {
        'title': 'A subpar commit by derp-diggity',
        'date': '08.02.2018',
        'description': 'Initial commit with some blah blah blah...',
    }]

    params = {
        'active': 'dashboard',
        'title': _('Grant Details'),
        'grant': grant,
        'keywords': get_keywords(),
        'is_admin': grant.admin_profile.id == profile.id,
        'activity': activity_data,
        'gh_activity': gh_data,
    }
    return TemplateResponse(request, 'grants/detail.html', params)


def grant_new(request):
    """Handle new grant."""
    profile = request.user.profile if request.user.is_authenticated else None

    if request.method == 'POST':
        logo = request.FILES.get('input_image', None)
        # TODO: Include milestones, frequency_unit, and team_members
        grant_kwargs = {
            'title': request.POST.get('input_name', ''),
            'description': request.POST.get('description', ''),
            'reference_url': request.POST.get('reference_url'),
            'admin_address': request.POST.get('admin_address', ''),
            'frequency': request.POST.get('frequency', 30),
            'token_address': request.POST.get('denomination', ''),
            'amount_goal': request.POST.get('amount_goal', 0),
            'transaction_hash': request.POST.get('transaction_hash', ''),
            'contract_address': request.POST.get('contract_address', ''),
            'network': request.POST.get('network', 'mainnet'),
            'admin_profile': profile,
            'logo': logo,
        }
        grant = Grant.objects.create(**grant_kwargs)
        return redirect(reverse('grants:details', args=(grant.pk, )))

    grant = {}
    params = {
        'active': 'grants',
        'title': _('New Grant'),
        'grant': grant,
        'keywords': get_keywords(),
    }

    return TemplateResponse(request, 'grants/new.html', params)


def grant_fund(request, grant_id):
    """Handle grant funding."""
    try:
        grant = Grant.objects.get(pk=grant_id)
    except Grant.DoesNotExist:
        raise Http404

    profile = request.user.profile if request.user.is_authenticated else None
    # make sure a user can only create one subscription per grant
    if request.method == 'POST':
        subscription = Subscription()
        # subscriptionHash and ContributorSignature will be given from smartcontracts and web3
        # subscription.subscriptionHash = request.POST.get('input_name')
        # subscription.contributorSignature = request.POST.get('description')
        # Address will come from web3 instance
        # subscription.contributorAddress = request.POST.get('reference_url')
        subscription.amount_per_period = request.POST.get('amount_per_period')
        # subscription.tokenAddress = request.POST.get('denomination')
        subscription.gas_price = request.POST.get('gas_price')
        # network will come from web3 instance
        # subscription.network = request.POST.get('amount_goal')
        subscription.contributor_profile = profile
        subscription.grant = grant
        subscription.save()
    else:
        subscription = {}

    params = {
        'active': 'dashboard',
        'title': _('Fund Grant'),
        'subscription': subscription,
        'grant': grant,
        'keywords': get_keywords(),
    }
    return TemplateResponse(request, 'grants/fund.html', params)


def subscription_cancel(request, subscription_id):
    """Handle the cancellation of a grant subscription."""
    subscription = Subscription.objects.select_related('grant').get(pk=subscription_id)
    grant = getattr(subscription, 'grant', None)

    if request.method == 'POST':
        subscription.status = False
        subscription.save()

    params = {
        'title': _('Cancel Grant Subscription'),
        'subscription': subscription,
        'grant': grant,
        'keywords': get_keywords(),
    }

    return TemplateResponse(request, 'grants/cancel.html', params)
