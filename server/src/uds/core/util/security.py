import secrets
import random
from datetime import datetime, timedelta
import ipaddress
import typing
import logging
import ssl

from django.conf import settings

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import certifi
import requests
import requests.adapters

logger = logging.getLogger(__name__)

KEY_SIZE = 4096
SECRET_SIZE = 32


try:
    # Ensure that we do not get warnings about self signed certificates and so
    import requests.packages.urllib3  # type: ignore

    requests.packages.urllib3.disable_warnings()  # type: ignore  # pylint: disable=no-member
except Exception:  # nosec: simple check for disabling warnings,
    # Igonre if we cannot disable warnings
    pass


def selfSignedCert(ip: str) -> typing.Tuple[str, str, str]:
    """
    Generates a self signed certificate for the given ip.
    This method is mainly intended to be used for generating/saving Actor certificates.
    UDS will check that actor server certificate is the one generated by this method.
    """
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=KEY_SIZE,
        backend=default_backend(),
    )
    # Create a random password for private key
    password = secrets.token_hex(SECRET_SIZE)

    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, ip)])
    san = x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(ip))])

    basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)  # self signed, its Issuer DN must match its Subject DN.
        .public_key(key.public_key())
        .serial_number(random.SystemRandom().randint(0, 1 << 64))
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=10 * 365))
        .add_extension(basic_contraints, False)
        .add_extension(san, False)
        .sign(key, hashes.SHA256(), default_backend())
    )

    return (
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                password.encode()
            ),
        ).decode(),
        cert.public_bytes(encoding=serialization.Encoding.PEM).decode(),
        password,
    )


def createClientSslContext(verify: bool = True) -> ssl.SSLContext:
    """
    Creates a SSLContext for client connections.

    Args:
        verify: If True, the server certificate will be verified. (Default: True)

    Returns:
        A SSLContext object.
    """
    sslContext = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, cafile=certifi.where()
    )
    if not verify:
        sslContext.check_hostname = False
        sslContext.verify_mode = ssl.VerifyMode.CERT_NONE

    # Disable TLS1.0 and TLS1.1, SSLv2 and SSLv3 are disabled by default
    # Next line is deprecated in Python 3.7
    # sslContext.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
    if hasattr(settings, 'SECURE_MIN_TLS_VERSION') and settings.SECURE_MIN_TLS_VERSION:
        # format is "1.0, 1.1, 1.2 or 1.3", convert to ssl.TLSVersion.TLSv1_0, ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_2 or ssl.TLSVersion.TLSv1_3
        sslContext.minimum_version = getattr(
            ssl.TLSVersion, 'TLSv' + settings.SECURE_MIN_TLS_VERSION.replace('.', '_')
        )
    else:
        sslContext.minimum_version = ssl.TLSVersion.TLSv1_2

    sslContext.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
    if hasattr(settings, 'SECURE_CIPHERS') and settings.SECURE_CIPHERS:
        sslContext.set_ciphers(settings.SECURE_CIPHERS)

    return sslContext


def checkCertificateMatchPrivateKey(*, cert: str, key: str) -> bool:
    """
    Checks if a certificate and a private key match.
    All parameters must be keyword arguments.
    Borh must be in PEM format.
    """
    try:
        public_cert = (
            x509.load_pem_x509_certificate(cert.encode(), default_backend())
            .public_key()
            .public_bytes(
                format=serialization.PublicFormat.PKCS1,
                encoding=serialization.Encoding.PEM,
            )
        )
        public_key = (
            serialization.load_pem_private_key(
                key.encode(), password=None, backend=default_backend()
            )
            .public_key()
            .public_bytes(
                format=serialization.PublicFormat.PKCS1,
                encoding=serialization.Encoding.PEM,
            )
        )
        return public_cert == public_key
    except Exception:
        # Not intended to show kind of error, just to return False if the certificate does not match the key
        # Even if the key or certificate is not valid, we only want a True if they match, False otherwise
        return False


def secureRequestsSession(
    *, verify: typing.Union[str, bool] = True
) -> 'requests.Session':
    '''
    Generates a requests.Session object with a custom adapter that uses a custom SSLContext.
    This is intended to be used for requests that need to be secure, but not necessarily verified.
    Removes the support for TLS1.0 and TLS1.1, and disables SSLv2 and SSLv3. (done in @createClientSslContext)

    Args:
        verify: If True, the server certificate will be verified. (Default: True)

    Returns:
        A requests.Session object.
    '''

    # Copy verify value
    lverify = verify

    class UDSHTTPAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs) -> None:
            kwargs["ssl_context"] = createClientSslContext(verify=verify is True)

            # See urllib3.poolmanager.SSL_KEYWORDS for all available keys.
            return super().init_poolmanager(*args, **kwargs)

        def cert_verify(self, conn, url, verify, cert) -> None:
            """Verify a SSL certificate. This method should not be called from user
            code, and is only exposed for use when subclassing the HTTPAdapter class
            """

            # If lverify is an string, use it even if verify is False
            # if not, use verify value
            if not isinstance(verify, str):
                verify = lverify

            # logger.info('Connection info: %s', conn)
            # for k, v in conn.__dict__.items():
            #     logger.info('Connection info: %s = %s', k, v)

            super().cert_verify(conn, url, verify, cert)

    session = requests.Session()
    session.mount("https://", UDSHTTPAdapter())

    return session
