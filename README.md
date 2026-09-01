# ChirpStack and XRepo LoRaWAN webhook

This repository runs the [ChirpStack](https://www.chirpstack.io) open-source
LoRaWAN Network Server (v4) together with the XRepo HTTP webhook. One Docker
Compose project starts the LoRaWAN services and the API that persists decoded
uplinks in the configured XRepo SQL Server database.

## Directory layout

* `docker-compose.yml`: the docker-compose file containing the services
* `configuration/chirpstack`: directory containing the ChirpStack configuration files
* `configuration/chirpstack-gateway-bridge`: directory containing the ChirpStack Gateway Bridge configuration
* `configuration/mosquitto`: directory containing the Mosquitto (MQTT broker) configuration
* `configuration/postgresql/initdb/`: directory containing PostgreSQL initialization scripts
* `api-webhook/`: FastAPI webhook and its SQL Server ODBC image definition
* `.env.example`: non-secret template for the XRepo SQL Server connection

## Configuration

This setup is pre-configured for all regions. You can either connect a ChirpStack Gateway Bridge
instance (v3.14.0+) to the MQTT broker (port 1883) or connect a Semtech UDP Packet Forwarder.
Please note that:

* You must prefix the MQTT topic with the region.
  Please see the region configuration files in the `configuration/chirpstack` for a list
  of topic prefixes (e.g. eu868, us915_0, au915_0, as923_2, ...).
* The protobuf marshaler is configured.

This setup also comes with two instances of the ChirpStack Gateway Bridge. One
is configured to handle the Semtech UDP Packet Forwarder data (port 1700), the
other is configured to handle the Basics Station protocol (port 3001). Both
instances are by default configured for EU868 (using the `eu868` MQTT topic
prefix).

### Reconfigure regions

ChirpStack has at least one configuration of each region enabled. You will find
the list of `enabled_regions` in `configuration/chirpstack/chirpstack.toml`.
Each entry in `enabled_regions` refers to the `id` that can be found in the
`region_XXX.toml` file. This `region_XXX.toml` also contains a `topic_prefix`
configuration which you need to configure the ChirpStack Gateway Bridge
UDP instance (see below).

#### ChirpStack Gateway Bridge (UDP)

Within the `docker-compose.yml` file, you must replace the `eu868` prefix in the
`INTEGRATION__..._TOPIC_TEMPLATE` configuration with the MQTT `topic_prefix` of
the region you would like to use (e.g. `us915_0`, `au915_0`, `in865`, ...).

#### ChirpStack Gateway Bridge (Basics Station)

Within the `docker-compose.yml` file, you must update the configuration file
that the ChirpStack Gateway Bridge instance must used. The default is
`chirpstack-gateway-bridge-basicstation-eu868.toml`. For available
configuration files, please see the `configuration/chirpstack-gateway-bridge`
directory.

# Data persistence

PostgreSQL and Redis data is persisted in Docker volumes, see the `docker-compose.yml`
`volumes` definition.

## Requirements

Before using this `docker-compose.yml` file, make sure you have [Docker](https://www.docker.com/community-edition)
installed.

## Importing device repository

To import the [chirpstack-device-profiles](https://github.com/chirpstack/chirpstack-device-profiles)
repository (optional step), run the following command:

```bash
make import-device-profiles
```

This will clone the `chirpstack-device-profiles` repository and execute the import command of ChirpStack.
Please note that for this step you need to have the `make` command installed.

## Usage

Create the local runtime configuration and set it to the production XRepo
database values. The `.env` file is ignored by Git and must never be
committed:

```bash
cp .env.example .env
# Edit .env with the production XRepo SQL Server connection values.
docker compose up -d --build
docker compose ps
```

After all the components have been initialized and started, you should be able
to open http://localhost:8080/ in your browser. The webhook health endpoint is
available from the Docker host only:

```bash
curl --fail http://127.0.0.1:3188/health
docker compose logs -f api-webhook
```

Stop the complete local stack with:

```bash
docker compose down
```

This command preserves the `postgresqldata` and `redisdata` volumes. Use
`docker compose down --volumes` only when intentionally deleting ChirpStack
data.

## ChirpStack HTTP integration

Create an HTTP integration for the ChirpStack application that owns the target
device and enable the `up` event. Use this URL:

```text
http://api-webhook:8000/webhooks/lorawan
```

`api-webhook` is the Docker Compose service name. ChirpStack resolves it
inside the Compose network, so no external Docker network, fixed IP address,
or deploy script is required.

The example includes the [ChirpStack REST API](https://github.com/chirpstack/chirpstack-rest-api).
You should be able to access the UI by opening http://localhost:8090 in your browser.

**Note:** It is recommended to use the [gRPC](https://www.chirpstack.io/docs/chirpstack/api/grpc.html)
interface over the [REST](https://www.chirpstack.io/docs/chirpstack/api/rest.html) interface.
