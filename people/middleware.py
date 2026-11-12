from django.utils import timezone

from .devices import COOKIE_NAME, SEEN_INTERVAL, find_device, remember_device
from .models import Device


class DeviceMiddleware:
    """
    Recognise the device a request comes from.

    Sets `request.device` to the allowed device, or to None. While a device is in use,
    its "last seen" time and its cookie are renewed about once an hour.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.COOKIES.get(COOKIE_NAME)
        device = find_device(token)
        request.device = device

        renew = False
        if device is not None:
            now = timezone.now()
            if device.last_seen_at is None or now - device.last_seen_at > SEEN_INTERVAL:
                Device.objects.filter(pk=device.pk).update(last_seen_at=now)
                renew = True

        response = self.get_response(request)
        if renew:
            remember_device(response, token)
        return response
