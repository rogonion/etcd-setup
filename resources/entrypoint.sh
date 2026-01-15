#!/bin/bash
set -e

if [ "${1#-}" != "$1" ]; then
    set -- etcd "$@"
fi

if [ "$1" = "etcd" ] || [ "$#" -eq 0 ]; then

    : "${ETCD_DATA_DIR:=/usr/local/etcd/data}"
    export ETCD_DATA_DIR

    THIS_HOST=$(hostname)

    : "${ETCD_LISTEN_CLIENT_URLS:=http://0.0.0.0:2379}"
    : "${ETCD_LISTEN_PEER_URLS:=http://0.0.0.0:2380}"

    : "${ETCD_ADVERTISE_CLIENT_URLS:=http://${THIS_HOST}:2379}"
    : "${ETCD_INITIAL_ADVERTISE_PEER_URLS:=http://${THIS_HOST}:2380}"

    export ETCD_LISTEN_CLIENT_URLS ETCD_LISTEN_PEER_URLS
    export ETCD_ADVERTISE_CLIENT_URLS ETCD_INITIAL_ADVERTISE_PEER_URLS

    if [ -z "$ETCD_INITIAL_CLUSTER" ]; then
        echo "Info: ETCD_INITIAL_CLUSTER not set. Defaulting to standalone mode."
        export ETCD_INITIAL_CLUSTER="default=${ETCD_INITIAL_ADVERTISE_PEER_URLS}"
        export ETCD_INITIAL_CLUSTER_STATE="new"
        export ETCD_NAME="default"
    fi

    if [ "$#" -eq 0 ]; then
        set -- etcd
    fi
fi

# 3. Execute
exec "$@"