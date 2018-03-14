from payments.forms import PaymentForm


class HBLForm(PaymentForm):
    class Media:
        js = ('js/hbl.js',)
