from __future__ import unicode_literals

from urllib.error import URLError
from urllib.parse import urlencode

from django.http import HttpResponseRedirect

from .forms import HBLForm
from payments import PaymentError, PaymentStatus, RedirectNeeded
from payments.core import BasicProvider

from payments.forms import PaymentForm


class HBLProvider(BasicProvider):
    '''
    Himalayan Bank Payment Gateway Provider for django_payments
    '''

    def __init__(self, *args, **kwargs):
        self.secret_key = kwargs.pop('secret_key')
        self.gateway_id = kwargs.pop('gateway_id')
        self.endpoint = kwargs.pop('endpoint', 'https://hblpgw.2c2p.com/HBLPGW/Payment/Payment/Payment')
        super().__init__(*args, **kwargs)

    def get_form(self, payment, data=None):
        return PaymentForm(self.get_hidden_fields(payment),
                           self.endpoint, self._method)

    # def get_form(self, payment, data=None):
    #     if payment.status == PaymentStatus.WAITING:
    #         payment.change_status(PaymentStatus.INPUT)
    #     form = HBLForm(data=data, hidden_inputs=False, provider=self, payment=payment)
    #     if form.is_valid():
    #         new_status = form.cleaned_data['status']
    #         payment.change_status(new_status)
    #         new_fraud_status = form.cleaned_data['fraud_status']
    #         payment.change_fraud_status(new_fraud_status)
    # 
    #         gateway_response = form.cleaned_data.get('gateway_response')
    #         verification_result = form.cleaned_data.get('verification_result')
    #         if gateway_response or verification_result:
    #             if gateway_response == '3ds-disabled':
    #                 # Standard request without 3DSecure
    #                 pass
    #             elif gateway_response == '3ds-redirect':
    #                 # Simulate redirect to 3DS and get back to normal
    #                 # payment processing
    #                 process_url = payment.get_process_url()
    #                 params = urlencode(
    #                     {'verification_result': verification_result})
    #                 redirect_url = '%s?%s' % (process_url, params)
    #                 raise RedirectNeeded(redirect_url)
    #             elif gateway_response == 'failure':
    #                 # Gateway raises error (HTTP 500 for example)
    #                 raise URLError('Opps')
    #             elif gateway_response == 'payment-error':
    #                 raise PaymentError('Unsupported operation')
    # 
    #         if new_status in [PaymentStatus.PREAUTH, PaymentStatus.CONFIRMED]:
    #             raise RedirectNeeded(payment.get_success_url())
    #         raise RedirectNeeded(payment.get_failure_url())
    #     return form

    def get_hidden_fields(self, payment):
        payment.save()
        # return_url = self.get_return_url(payment)
        currency_codes = {
            'NPR': 524,
            'USD': 840
        }
        currency_code = currency_codes.get(payment.currency)
        if not currency_code:
            raise PaymentError('Unsupported Currency for the Gateway')
        padded_amount = str(int(payment.get_total_price()[0] * 100)).zfill(12)
        # padded_amount = str(int(1 * 100)).zfill(12)
        data = {
            'paymentGatewayID': self.gateway_id,
            'currencyCode': currency_code,
            'productDesc': "Payment #%s" % (payment.pk,),
            'invoiceNo': payment.order_id,
            'Amount': padded_amount,
            # 'Nonsecure': 'Y'
        }
        return data

    def process_data(self, payment, request):
        verification_result = request.GET.get('verification_result')
        if verification_result:
            payment.change_status(verification_result)
        if payment.status in [PaymentStatus.CONFIRMED, PaymentStatus.PREAUTH]:
            return HttpResponseRedirect(payment.get_success_url())
        return HttpResponseRedirect(payment.get_failure_url())

    def capture(self, payment, amount=None):
        payment.change_status(PaymentStatus.CONFIRMED)
        return amount

    def release(self, payment):
        return None

    def refund(self, payment, amount=None):
        return amount or 0
