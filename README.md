# etcd-setup

A utility for creating a customized, rootless [etcd](https://etcd.io/) container image. This project builds a "lean"
image based on the official binary distribution, packaged on a modern OpenSUSE base without unnecessary runtime bloat.

**Base Image:** [openSUSE Leap 16.0](https://registry.opensuse.org/cgi-bin/cooverview)  
**etcd Version:** 3.5.11 (Official Binary Release)

## Pre-requisites

**OS:** Linux-based.

<table>
    <caption>Required Tools</caption>
    <thead>
        <tr>
            <th>Package</th>
            <th>Version</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Python</td>
            <td>3.13+</td>
            <td>
                <p>Core language the CLI tool is written in.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://python-poetry.org/docs/">Poetry</a></td>
            <td>2.2.1+</td>
            <td>
                <p>Project dependency manager.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://buildah.io/">Buildah</a></td>
            <td>1.41.5+</td>
            <td>
                <p>Used to programmatically create OCI-compliant container images without a daemon.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://taskfile.dev/">Taskfile</a></td>
            <td>3.46.3+</td>
            <td>
                <p>Optional. You can use the provided <a href="taskw">shell script wrapper</a> (<code>./taskw</code>) which scopes the binary to the project.</p>
            </td>
        </tr>
    </tbody>
</table>

## Usage

List available tasks:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY --list
```

Setup python virtual environment and install dependencies:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY init
```

View CLI tool options and build help:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- --help
```

### Example

Build the core artifact (downloads and extracts the Etcd distribution):

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- containers core build
```

Build the runtime image (sets up users, copies artifacts, and configuring entrypoints):

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- containers runtime build
```

Run the built container using `podman`:

- Standalone Mode (Single node, auto-configured):
  ```shell
  #!/bin/bash
  
  CONTAINER="etcd-standalone"
  NETWORK="tumbleweed"
  NETWORK_ALIAS="etcd-node-1"
  CONTAINER_UID=1001
  CONTAINER_GID=1001
  
  # Ports: 2379 (Client), 2380 (Peer)
  PORT_CLIENT=2379
  PORT_PEER=2380
  
  IMAGE="localhost/etcd-setup-runtime:3.5.11"
  
  # Create volume for persistence
  podman volume exists etcd_data || podman volume create etcd_data
  podman unshare chown -R $CONTAINER_UID:$CONTAINER_GID $(podman volume inspect etcd_data --format '{{.Mountpoint}}')
  
  podman run -d \
  --name $CONTAINER \
  --network $NETWORK \
  --network-alias $NETWORK_ALIAS \
  --user $CONTAINER_UID:$CONTAINER_GID \
  -p $PORT_CLIENT:2379 \
  -p $PORT_PEER:2380 \
  -v etcd_data:/usr/local/etcd/data \
  -e "ETCD_NAME=standalone" \
  -e "ETCD_ADVERTISE_CLIENT_URLS=http://localhost:2379" \
  $IMAGE
  ```
- Cluster Mode (3 Separate Nodes):
  ```shell
  # 1. Start Node 1
  CONTAINER="etcd-1"
  NETWORK="tumbleweed"
  NETWORK_ALIAS="etcd-1"
  IMAGE="localhost/etcd-setup-runtime:3.5.11"
  TOKEN="my-etcd-token"
  CLUSTER="etcd-1=http://etcd-1:2380,etcd-2=http://etcd-2:2380,etcd-3=http://etcd-3:2380"
  
  podman run -d --name $CONTAINER --network $NETWORK --network-alias $NETWORK_ALIAS \
  -e ETCD_NAME=$CONTAINER \
  -e ETCD_INITIAL_CLUSTER_TOKEN=$TOKEN \
  -e ETCD_INITIAL_CLUSTER=$CLUSTER \
  -e ETCD_INITIAL_CLUSTER_STATE=new \
  -e ETCD_LISTEN_PEER_URLS=[http://0.0.0.0:2380](http://0.0.0.0:2380) \
  -e ETCD_LISTEN_CLIENT_URLS=[http://0.0.0.0:2379](http://0.0.0.0:2379) \
  -e ETCD_ADVERTISE_CLIENT_URLS=http://$NETWORK_ALIAS:2379 \
  -e ETCD_INITIAL_ADVERTISE_PEER_URLS=http://$NETWORK_ALIAS:2380 \
  $IMAGE
  
  # 2. Start Node 2
  CONTAINER="etcd-2"
  NETWORK_ALIAS="etcd-2"
  
  podman run -d --name $CONTAINER --network $NETWORK --network-alias $NETWORK_ALIAS \
  -e ETCD_NAME=$CONTAINER \
  -e ETCD_INITIAL_CLUSTER_TOKEN=$TOKEN \
  -e ETCD_INITIAL_CLUSTER=$CLUSTER \
  -e ETCD_INITIAL_CLUSTER_STATE=new \
  -e ETCD_LISTEN_PEER_URLS=[http://0.0.0.0:2380](http://0.0.0.0:2380) \
  -e ETCD_LISTEN_CLIENT_URLS=[http://0.0.0.0:2379](http://0.0.0.0:2379) \
  -e ETCD_ADVERTISE_CLIENT_URLS=http://$NETWORK_ALIAS:2379 \
  -e ETCD_INITIAL_ADVERTISE_PEER_URLS=http://$NETWORK_ALIAS:2380 \
  $IMAGE
  
  # 3. Start Node 3 (Identical Logic)
  CONTAINER="etcd-3"
  NETWORK_ALIAS="etcd-3"
  
  podman run -d --name $CONTAINER --network $NETWORK --network-alias $NETWORK_ALIAS \
  -e ETCD_NAME=$CONTAINER \
  -e ETCD_INITIAL_CLUSTER_TOKEN=$TOKEN \
  -e ETCD_INITIAL_CLUSTER=$CLUSTER \
  -e ETCD_INITIAL_CLUSTER_STATE=new \
  -e ETCD_LISTEN_PEER_URLS=[http://0.0.0.0:2380](http://0.0.0.0:2380) \
  -e ETCD_LISTEN_CLIENT_URLS=[http://0.0.0.0:2379](http://0.0.0.0:2379) \
  -e ETCD_ADVERTISE_CLIENT_URLS=http://$NETWORK_ALIAS:2379 \
  -e ETCD_INITIAL_ADVERTISE_PEER_URLS=http://$NETWORK_ALIAS:2380 \
  $IMAGE
  ```

## Application Container Image Features

### Ports

<table> <thead> <th>Port</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>2379</code></td> <td><strong>Client API (gRPC/HTTP).</strong> Used by applications (Pulsar, Kubernetes, your Go Ingress) to read/write data.</td> </tr> <tr> <td><code>2380</code></td> <td><strong>Peer Communication.</strong> Used by Etcd nodes to talk to each other (Raft Consensus). Do not expose this publicly.</td> </tr> </tbody> </table>

### Volumes

<table> <thead> <th>Path</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>/usr/local/etcd/data</code></td> <td><strong>Data Directory.</strong> Stores the Write-Ahead Log (WAL) and Snapshots. <strong>Critical:</strong> Ensure you mount a volume here to persist data across restarts.</td> </tr> </tbody> </table>

### Environment variables

Configuration is handled via standard Etcd environment variables passed at runtime. The entrypoint script will
automatically set defaults if these are omitted.

<table> <thead> <th>Name</th> <th>Example</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>ETCD_NAME</code></td> <td><code>etcd-node-1</code></td> <td>Human-readable name for this member.</td> </tr> <tr> <td><code>ETCD_INITIAL_CLUSTER</code></td> <td><code>node1=http://node1:2380,node2=http://node2:2380</code></td> <td>List of all members in the cluster. Required for multi-node setup.</td> </tr> <tr> <td><code>ETCD_ADVERTISE_CLIENT_URLS</code></td> <td><code>http://localhost:2379</code></td> <td>List of this member's client URLs to advertise to the public.</td> </tr> <tr> <td><code>ETCD_DATA_DIR</code></td> <td><code>/custom/data/path</code></td> <td>Override where data is stored inside the container (Default: <code>/usr/local/etcd/data</code>).</td> </tr> </tbody> </table>