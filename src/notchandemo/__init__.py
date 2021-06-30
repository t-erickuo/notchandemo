import threading
import typing
import uuid

import grpc

from azure.core.polling.base_polling import LROBasePolling
from azure.mgmt.core.polling.arm_polling import ARMPolling

from . import sessionprotocol
from . import LightsaberService_pb2 as messages
from . import LightsaberService_pb2_grpc as service

__all__ = [
    "GrpcDemoSession",
    "make_notification_session_aware",
    "apply_magic_to_make_faster",
]
class GrpcDemoSession(sessionprotocol.SessionProtocol):

    SELF_SIGNED_CERT = b"""
-----BEGIN CERTIFICATE-----
MIIDajCCAlKgAwIBAgIQDNxeNw93TcqTYsaPxeNoZDANBgkqhkiG9w0BAQsFADAy
MTAwLgYDVQQDEydscnAtcmctZWFzdHVzLmVhc3R1cy5jbG91ZGFwcC5henVyZS5j
b20wHhcNMjEwNjE1MjAzNjE2WhcNMjIwNjE1MjA0NjE2WjAyMTAwLgYDVQQDEyds
cnAtcmctZWFzdHVzLmVhc3R1cy5jbG91ZGFwcC5henVyZS5jb20wggEiMA0GCSqG
SIb3DQEBAQUAA4IBDwAwggEKAoIBAQDU6dmkHxrzT3ckUOKe8GMpFOP1bKbo+Hz4
wLymCDbnGmFqt8BlJmLguiB25NlqDgNzbUjfUu4u//z1Kony4GA/XJ+S8eDo5z9f
P6tdHSslFQwOv+wl8bXcqQGlDm1DNfCP6DikbEIKITfYlnTgEXFyNxk0GllgtLuX
X1EUKgODVMQLRdcgEs79ZsAtQbR35044Ye+2FhQcuxW+klgmHW34Y5AgFOReAS9e
N8OQitj1z3b9+TqQd1ib3XzrQixI9VF7ga+wAxu2XKV409mFf+KHxkRi6L2dQCe/
tggy6d/RMD3ecAVOTCirPOy86pGZ4iniHZ2/aexlYiloJ2shq7l9AgMBAAGjfDB6
MA4GA1UdDwEB/wQEAwIFoDAJBgNVHRMEAjAAMB0GA1UdJQQWMBQGCCsGAQUFBwMB
BggrBgEFBQcDAjAfBgNVHSMEGDAWgBQUC3Fe0LUYiRlwCgVdon2NvQosOTAdBgNV
HQ4EFgQUFAtxXtC1GIkZcAoFXaJ9jb0KLDkwDQYJKoZIhvcNAQELBQADggEBAMGS
Eq9kzkZ8M1svumm2z2Rr8s/zG+0SaGw9mhX6KlZ4fhRLglRtkyAxbRWY2rjvxTGG
tSaHjHT2zcMPssiOhniOuhgIk4ocIonEc9iWlhF45TEInRH/sClz72MZBo8/35wZ
nSFORVr3w2ax0KukylFN3jLs2T4GruHk5P8y115X561VrOc05W4ZGuQIpb/wgkKN
5N8cS7cLedDkgp/1qJzFJPTu23sfs/KXcus7G8JKqSp7eIZT0238yEka+cx8qgx5
snaKGI4WXpNY5NgXCxBlfOD5kI6b1H/NAgo1ClKzHch2wNUvTLMrinYN1QmuP0at
3ZBzVXfg9Vk6tuMj1qI=
-----END CERTIFICATE-----
    """

    def __init__(self, host, session_id):
        super(GrpcDemoSession, self).__init__()
        self.host = host
        self.session_id = session_id
        self.thread = threading.Thread(target=self.run, daemon=True)
        self._channel = None
        self._stub = None
        self.open()
        self.thread.start()
        # TODO: fix race condition with connecting & completion of
        # notification...

    def open(self):
        credentials = grpc.ssl_channel_credentials(GrpcDemoSession.SELF_SIGNED_CERT)
        self._channel = grpc.secure_channel(self.host, credentials=credentials)
        self._stub = service.LightsaberServiceStub(self._channel, self.session_id)
    
    def run(self):
        try:
            for notification in self._stub.SubscribeSession(
                    messages.SubscriptionRequest(sessionId=self.session_id)
                ):
                try:
                    request_id = notification.id
                    self.on_completion(request_id, notification)
                except KeyError:
                    pass
        except Exception as e:
            print(f"channel failed - {e}")
        finally:
            self._channel.close()

    def extract_notification(self, response, **kwargs):
        request_id = response.request.headers['x-ms-client-request-id']
        return request_id

    def close(self):
        try:
            self._channel.close()
        finally:
            super(GrpcDemoSession, self).close()
        

class SessionArmPollerMixin(LROBasePolling):

    def _delay(self, *args, **kwargs):
        try:
            notification_channel = self._client._notification_channel
        except AttributeError:
            notification_channel = None

        if notification_channel and not getattr(self, '_notification_waited_on', False):
            notification_channel.wait(response=self._pipeline_response.http_response)
            self._notification_waited_on = True
        else:
            retval = super(SessionArmPollerMixin, self)._delay(*args, **kwargs)
            return retval

def make_notification_session_aware(client_type):
    class SessionManagementClient(client_type):

        def __init__(self, *args, **kwargs):
            session = kwargs.pop('session', None)
            super(SessionManagementClient, self).__init__(*args, **kwargs)
            if session:
                self._client._notification_channel = session

    return SessionManagementClient

def apply_magic_to_make_faster():
    # Let's  inject our middle tier class. Dark, sweet magic!
    if not SessionArmPollerMixin in ARMPolling.__bases__:
        ARMPolling.__bases__ = (SessionArmPollerMixin,)

    import azure.mgmt.storage
    azure.mgmt.storage.StorageManagementClient = make_notification_session_aware(azure.mgmt.storage.StorageManagementClient)     
    import azure.mgmt.compute
    azure.mgmt.compute.ComputeManagementClient = make_notification_session_aware(azure.mgmt.compute.ComputeManagementClient)     
    
