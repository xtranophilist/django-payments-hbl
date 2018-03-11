django-payments-hbl
=====================

[Himalayan Bank](https://himalayanbank.com/hbl-introduces-enhanced-e-commerce-payment-gateway) Payment Gateway Provider for [django_payments](https://django-payments.readthedocs.org/)


Usage
==============

In your Django project settings:

```
PAYMENT_VARIANTS = {
    'default': ('django_hbl.HBLProvider', {
        'gateway_id': '<gateway/merchant_id>',
        'secret_key': '<your_secret_key>'
    })}
```



