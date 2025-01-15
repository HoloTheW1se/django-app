from datetime import datetime
from ipaddress import ip_address

from django.http import HttpRequest, HttpResponseForbidden


def set_useragent_on_request_middleware(get_response):

    print("initial call")

    def middleware(request: HttpRequest):
        print("before get response")
        request.user_agent = request.META["HTTP_USER_AGENT"]
        response = get_response(request)
        print("after get response")
        return response

    return middleware


class CountRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_count = 0
        self.responses_count = 0
        self.exceptions_count = 0

    def __call__(self, request: HttpRequest):
        self.requests_count += 1
        print("requests count", self.requests_count)
        response = self.get_response(request)
        self.responses_count += 1
        print("responses count", self.responses_count)
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        self.exceptions_count += 1
        print("got", self.exceptions_count, "exceptions so far")


class ThrottlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.log = {}

    def __call__(self, request: HttpRequest):
        ip_address = request.META.get("REMOTE_ADDR")
        current_time = datetime.now()

        if ip_address not in self.log:
            self.log[ip_address] = [current_time]
        else:
            last_request = self.log[ip_address][-1]
            interval = current_time - last_request

            if interval.total_seconds() < 10:
                return HttpResponseForbidden("Try later!", status=403)

            self.log[ip_address].append(current_time)

        response = self.get_response(request)
        return response
