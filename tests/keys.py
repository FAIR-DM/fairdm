"""A public key for tests that boot a production portal, which refuses to start without one."""

from pathlib import Path

#: An armoured RSA public key that can encrypt. Its private half was never kept.
BACKUP_PUBLIC_KEY = Path(__file__).with_name("backup-public-key.asc").read_text()
