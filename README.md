# OpenShift Upgrade Planner

Uses https://github.com/openshift/cincinnati to find the shortest upgrade path for an OpenShift cluster.

## Usage

./planner.py [ --architecture {amd64,aarch64,ppc64le,s390x} ] --from-version FROM_VERSION --to-version TO_VERSION

FROM_VERSION and TO_VERSION must be OpenShift semantic versions, eg 4.16.4 .
The default ARCH is amd64.
