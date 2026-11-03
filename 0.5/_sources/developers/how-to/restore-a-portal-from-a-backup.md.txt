# How to restore a portal from a backup

You bring a portal back from the encrypted backups it wrote, or you check that a backup restores by restoring it into a second, empty deployment. FairDM adds no restore command: you use the `listbackups`, `dbrestore` and `mediarestore` commands of django-dbbackup in a one-off container of the portal's own image.

## Before you start

- You hold the private key whose public half is the portal's [`BACKUP_PUBLIC_KEY`](back-up-a-portal.md#encrypt-the-backups), and its passphrase if it has one. The portal never holds it.
- You can reach the backup location from a container: the volume at `/var/lib/fairdm/backups`, or the bucket the portal writes to. The one-off container needs the portal's environment file, so it reads the same storage.
- The portal's database exists and is reachable, empty or not.

## Steps

1. List the backups. This works without the private key and without the scheduler running, so it is also the way to check that backups are being written at all.

   ```bash
   docker run --rm --env-file /etc/my-portal/portal.env \
     --volume my-portal-backups:/var/lib/fairdm/backups \
     my-portal python manage.py listbackups
   ```

   Each line is a file name and its date. Database backups end in `.psql.bin.gpg` and media backups in `.tar.gz.gpg`. Add `--content-type db` or `--content-type media` to list one kind. When the newest backup is older than the schedule says it should be, check the worker and beat first, as [How to back up a portal](back-up-a-portal.md#before-you-start) describes.

2. Stop the portal's web, worker and beat containers, so nothing writes to the database while you restore it.

3. Start a one-off container with the private key mounted, and import the key into the container's own gpg keyring. The key lives only as long as the container. Run the restore in the same container, so the next steps share the keyring.

   ```bash
   docker run --rm -it --env-file /etc/my-portal/portal.env \
     --volume my-portal-backups:/var/lib/fairdm/backups \
     --volume "$PWD/backups-private.asc:/tmp/backups-private.asc:ro" \
     my-portal sh
   ```

   ```bash
   gpg --import /tmp/backups-private.asc
   ```

4. Restore the database. With no file name, `dbrestore` takes the latest database backup; add `--input-filename` with a name from step 1 to take another one.

   ```bash
   python manage.py dbrestore --decrypt
   ```

   It asks you to confirm and, when the key has a passphrase, asks for it. A key with no passphrase takes an empty answer. It decrypts first, so a key that does not match stops the command before the database changes. The restore then runs in a single transaction and replaces what is in the database: the records are those of the moment the backup was written, and records added since are gone.

5. Restore the media. With no file name, `mediarestore` takes the latest media backup, and `--input-filename` takes another. Media archives are compressed, so add `--uncompress`.

   ```bash
   python manage.py mediarestore --decrypt --uncompress --replace
   ```

   `--replace` overwrites a file that already exists in the media storage with the one from the backup. Without it, such a file is left as it is. Files in the media storage that are not in the backup stay.

6. Leave the container with `exit`, then start the web, worker and beat containers again. Check that you can sign in and open a record.

Add `--noinput` to either command to skip the confirmation, such as in a script.

## Check a backup in a trial restore

A trial restore proves that a backup restores, with the key and the commands you would use in an emergency, and leaves the portal as it is. Run it in a separate, empty deployment.

1. Create a second deployment from the same image with its own PostgreSQL database, empty, on a server that has PostGIS. Give it its own environment file with the second database's `POSTGRES_*` values.

2. Give it its own backup location and its own media storage: a different volume at `/var/lib/fairdm/backups` and a different `/app/media` volume, or a different bucket. Never point it at the original portal's.

   ```{warning}
   Retention counts every file in the backup location, so a trial deployment that shares the original's location deletes the original's oldest backups when it writes one. `mediarestore --replace` writes into the media storage, so a trial deployment that shares the original's media overwrites the original's files.
   ```

3. Copy the backup file you want to try into the trial deployment's backup location.

4. Run steps 3 to 5 above against the trial deployment, in its own one-off container. Do not run step 2, as the original portal keeps running.

5. Start the trial deployment's web container and check that you can sign in and that the records and files you expect are there.

6. Remove the trial deployment's containers, volumes and database when you have finished. The original portal and its backups were never touched.

## If a restore fails

- `Decryption failed` means the private key in the container's keyring is not the one the backup was encrypted to, or the passphrase was wrong. The database and the media are unchanged. Compare the fingerprint of the key with `gpg --list-secret-keys`, and with the fingerprint of the `BACKUP_PUBLIC_KEY` the portal had when it wrote the backup.
- `There's no backup file available` means the backup location holds no backup of that kind that matches. Check step 1 against the same volume or bucket.
