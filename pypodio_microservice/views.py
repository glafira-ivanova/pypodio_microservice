from django.http import HttpResponse
from . import client_settings
from . import service


def get_conversion(request):
    stats = service.main()
    conversion = stats['converted_mp_percentage']
    return HttpResponse(conversion)


def get_logs(request):
    with open(client_settings.log_file, 'r') as log:
        return HttpResponse(log.read(), content_type='text/plain')
