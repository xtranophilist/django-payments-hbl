import hmac
import hashlib
import base64

from django.http import HttpResponseRedirect

from payments import PaymentError, PaymentStatus
from payments.core import BasicProvider

from payments.forms import PaymentForm


class HBLProvider(BasicProvider):
    """
    Himalayan Bank Payment Gateway Provider for django_payments
    """

    def get_token_from_request(self, payment, request):
        pass

    def __init__(self, *args, **kwargs):
        self.secret_key = kwargs.pop('secret_key')
        self.gateway_id = kwargs.pop('gateway_id')
        self.endpoint = kwargs.pop('endpoint', 'https://hblpgw.2c2p.com/HBLPGW/Payment/Payment/Payment')
        super().__init__(*args, **kwargs)

    def get_form(self, payment, data=None):
        return PaymentForm(self.get_hidden_fields(payment), self.endpoint, self._method)

    def get_hash(self, msg):
        dig = hmac.new(bytes(self.secret_key, 'latin-1'), msg=bytes(msg, 'latin-1'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()  # py3k-mode

    def get_hidden_fields(self, payment):
        payment.save()
        return_url = self.get_return_url(payment)
        currency_codes = {
            'NPR': 524,
            'USD': 840
        }
        currency_code = currency_codes.get(payment.currency)
        if not currency_code:
            raise PaymentError('Unsupported Currency for the Gateway')
        padded_amount = str(int(payment.get_total_price()[0] * 100)).zfill(12)
        # padded_amount = str(int(1 * 100)).zfill(12)
        non_secure = 'N'
        msg_hash = self.get_hash(str(self.gateway_id) + str(payment.order_id) + padded_amount + str(currency_code) + non_secure)
        data = {
            'paymentGatewayID': self.gateway_id,
            'currencyCode': currency_code,
            'productDesc': "Payment #%s" % (payment.pk,),
            'invoiceNo': payment.order_id,
            'Amount': padded_amount,
            'hash': msg_hash,
            # 'Nonsecure': non_secure,
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
