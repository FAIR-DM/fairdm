#!/bin/sh
# Publishes the base images of a release: <version> (runtime) and <version>-dev (development).
#
#   docker/publish.sh VERSION [REPOSITORY]
#
# VERSION is the image release's version, such as 1.2.0. REPOSITORY defaults to ghcr.io/fair-dm/fairdm.
# These environment variables name the local images to publish and the docker command:
#
#   RUNTIME_IMAGE      the runtime image (default: fairdm-base:ci)
#   DEVELOPMENT_IMAGE  the development image (default: fairdm-base:ci-dev)
#   DOCKER             the docker command (default: docker)
#
# A tag the registry already has is left alone, so a published tag never moves. A missing tag is
# pushed, so running the script again completes a release that stopped halfway. Only an answer of
# "not found" counts as missing. Any other answer, such as a refused connection or a refused
# login, stops the script before anything is pushed.
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: $0 VERSION [REPOSITORY]" >&2
  exit 2
fi

version=$1
repository=${2:-ghcr.io/fair-dm/fairdm}
docker=${DOCKER:-docker}
runtime_image=${RUNTIME_IMAGE:-fairdm-base:ci}
development_image=${DEVELOPMENT_IMAGE:-fairdm-base:ci-dev}

# exists REFERENCE: succeeds when the registry has it, fails when it answers "not found", and
# stops the script on any other answer.
exists() {
  if answer=$("$docker" buildx imagetools inspect "$1" 2>&1); then
    return 0
  fi
  case $answer in
    *"not found"*) return 1 ;;
  esac
  echo "cannot tell whether $1 exists:" >&2
  echo "$answer" >&2
  exit 1
}

# publish LOCAL_IMAGE REFERENCE EXISTS: push the local image as REFERENCE unless EXISTS is set.
publish() {
  if [ -n "$3" ]; then
    echo "$2 exists, left alone"
    return 0
  fi
  "$docker" tag "$1" "$2"
  "$docker" push "$2"
}

release=$repository:$version
development=$repository:$version-dev

# Ask about both tags before pushing either.
release_exists=
development_exists=
if exists "$release"; then release_exists=1; fi
if exists "$development"; then development_exists=1; fi

publish "$runtime_image" "$release" "$release_exists"
publish "$development_image" "$development" "$development_exists"
