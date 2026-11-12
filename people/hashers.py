from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PinHasher(PBKDF2PasswordHasher):
    """
    How PINs are stored.

    A PIN has at most eight digits, so no amount of hashing work protects it against
    someone who already holds the database. What protects it is the pause after repeated
    wrong tries (people/pins.py). The work is therefore kept small, so that checking a
    PIN on a Raspberry Pi does not keep people waiting at the PIN pad.
    """

    algorithm = "pin_pbkdf2_sha256"
    iterations = 150_000
