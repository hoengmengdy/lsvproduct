import os


class PaymentError(RuntimeError):
    pass


class CashOnDeliveryProvider:
    def initialize(self, order):
        return {"status": "pending", "reference": None}


class KHQRProvider:
    """Safe integration boundary for a future Bakong/KHQR SDK.

    Credentials must come from environment variables or a production secret
    manager. Payment callbacks must be signature-verified before changing an
    order's payment status.
    """
    def __init__(self):
        self.merchant_id = os.getenv("KHQR_MERCHANT_ID")
        self.api_base_url = os.getenv("KHQR_API_BASE_URL")

    def initialize(self, order):
        # No external payment is attempted until the provider is configured.
        return {"status": "pending", "reference": None}


def get_payment_provider(method):
    providers = {"cod": CashOnDeliveryProvider, "khqr": KHQRProvider}
    try:
        return providers[method]()
    except KeyError as exc:
        raise PaymentError("Unsupported payment method") from exc

