import hmac
import hashlib
import base64

from django.http import HttpResponseRedirect

from payments import PaymentError, PaymentStatus, FraudStatus
from payments.core import BasicProvider
from payments.forms import PaymentForm


class HBLProvider(BasicProvider):
    """
    Himalayan Bank Payment Gateway Provider for django_payments
    """

    CURRENCY_CODES = {
        'NPR': 524,
        'USD': 840
    }

    def get_token_from_request(self, payment, request):
        pass

    def __init__(self, *args, **kwargs):
        self.secret_key = kwargs.pop('secret_key')
        self.gateway_id = kwargs.pop('gateway_id')
        self.endpoint = kwargs.pop('endpoint', 'https://hblpgw.2c2p.com/HBLPGW/Payment/Payment/Payment')
        super().__init__(*args, **kwargs)

    def get_form(self, payment, data=None):
        return PaymentForm(self.get_hidden_fields(payment), self.endpoint, self._method, autosubmit=True)

    def get_hash(self, *args):
        msg = ''.join(map(str, args))
        dig = hmac.new(bytes(self.secret_key, 'latin-1'), msg=bytes(msg, 'latin-1'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()  # py3k-mode

    def get_amount(self, payment):
        # TODO Handle different django_payments versions
        return payment.get_total_price()[0]

    def get_amount_str(self, payment):
        return str(int(self.get_amount(payment) * 100)).zfill(12)

    def get_invoice_no(self, payment):
        return str(payment.order_id)

    def get_hidden_fields(self, payment):
        # return_url = self.get_return_url(payment)
        currency_code = self.CURRENCY_CODES.get(payment.currency)
        if not currency_code:
            raise PaymentError('Unsupported Currency for the Gateway')
        padded_amount = self.get_amount_str(payment)
        # padded_amount = str(int(1 * 100)).zfill(12)
        non_secure = 'N'
        # HashValue = merchantID + invoiceNumber +  amount + currencyCode + nonSecure
        request_hash = self.get_hash(self.gateway_id, payment.order_id, padded_amount, currency_code, non_secure)
        data = {
            'paymentGatewayID': self.gateway_id,
            'currencyCode': currency_code,
            'productDesc': "Payment #%s" % (payment.pk,),
            'invoiceNo': self.get_invoice_no(payment),
            'Amount': padded_amount,
            'hashValue': request_hash,
            'Nonsecure': non_secure,
        }
        return data

    def process_data(self, payment, request):
        response_code = request.GET.get('respCode')
        fraud_code = request.GET.get('fraudCode')
        payment.fraud_status = FraudStatus.ACCEPT if fraud_code == '00' else FraudStatus.REJECT
        if response_code == '00':
            # check hash
            # HashValue = paymentGatewayID + respCode + fraudCode + Pan + Amount + invoiceNo + tranRef + approvalCode
            # + Eci + dateTime + Status
            response_hash = self.get_hash(self.gateway_id, '00', fraud_code, request.GET.get('pan'), self.get_amount_str(payment),
                                          self.get_invoice_no(payment), request.GET.get('tranRef'),
                                          request.GET.get('approvalCode'),
                                          request.GET.get('eci'), request.GET.get('dateTime'), request.GET.get('status'))
            if response_hash == request.GET.get('hashValue'):
                self.capture(payment)
                return HttpResponseRedirect(payment.get_success_url())
            else:
                payment.change_status(PaymentStatus.ERROR)
        else:
            payment.change_status(PaymentStatus.REJECTED)
        return HttpResponseRedirect(payment.get_failure_url())

    def capture(self, payment, amount=None):
        payment.captured_amount = self.get_amount(payment)
        payment.change_status(PaymentStatus.CONFIRMED)
        return amount
