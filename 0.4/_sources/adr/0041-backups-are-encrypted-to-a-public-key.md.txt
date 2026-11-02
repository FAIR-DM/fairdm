# ADR 0041 — Backups are encrypted to a public key

**Status:** accepted

## Decision

Every backup, database and media alike, is encrypted with GPG to the public key in
`BACKUP_PUBLIC_KEY`. The portal holds only the public key. The private key is kept elsewhere and
is used only to restore. A production portal with no key, or with a key that cannot encrypt,
refuses to start (`fairdm.E700`, `fairdm.E701`), and so does one given a private key. A
development portal with no key writes unencrypted backups.

## Why

A backup holds every record and file of the portal, so it is encrypted by default. FairDM never
supplies a working default for a security-critical value, and a production portal that leaves one
out refuses to start. An encryption key is such a value. With only the public key on the portal,
a portal that is compromised does not expose its own past backups.

Development has no key to manage, so the development stack can take and restore backups as they
are.

## Revisit if

A deployment needs backups that can be restored without anyone holding a private key, for
instance through a storage service's own encryption.
