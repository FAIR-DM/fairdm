#!/bin/sh
# Prints the version of the next image release.
#
#   docker/next-version.sh BUMP
#
# BUMP is patch, minor or major, counted on from the newest image-v<version> tag in the current
# repository (0.0.0 when there is none), or an explicit <major>.<minor>.<patch> above that newest
# version. FairDM's own v<version> tags are not image releases and are ignored. Anything else is
# refused with a message on stderr and nothing on stdout.
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 patch|minor|major|<major>.<minor>.<patch>" >&2
  exit 2
fi
bump=$1

newest=$(git tag --list 'image-v*' | sed 's/^image-v//' \
  | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1)
newest=${newest:-0.0.0}
major=${newest%%.*}
rest=${newest#*.}
minor=${rest%%.*}
patch=${rest#*.}

case $bump in
  patch) echo "$major.$minor.$((patch + 1))" ;;
  minor) echo "$major.$((minor + 1)).0" ;;
  major) echo "$((major + 1)).0.0" ;;
  *)
    if ! printf '%s\n' "$bump" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
      echo "$bump is not patch, minor, major or a version like 1.2.3" >&2
      exit 1
    fi
    higher=$(printf '%s\n%s\n' "$newest" "$bump" | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1)
    if [ "$bump" = "$newest" ] || [ "$higher" != "$bump" ]; then
      echo "$bump is not above the newest image release, $newest" >&2
      exit 1
    fi
    echo "$bump"
    ;;
esac
