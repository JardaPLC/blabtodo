from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from household.backups import snapshot_before_update


class Command(BaseCommand):
    help = (
        "Keep a copy of the database as it was before this version first started. "
        "Run by the container before it brings the database up to date."
    )

    def handle(self, *args, **options):
        # A snapshot that cannot be written must not stop the app from starting.
        try:
            snapshot = snapshot_before_update(settings.APP_VERSION)
        except (DatabaseError, OSError) as error:
            self.stderr.write(f"The snapshot before the update could not be written: {error}")
            return
        if snapshot is None:
            self.stdout.write("No snapshot needed.")
        else:
            self.stdout.write(f"Snapshot written: {snapshot}")
