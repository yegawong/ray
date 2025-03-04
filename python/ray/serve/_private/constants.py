import os
from enum import Enum

#: Used for debugging to turn on DEBUG-level logs
DEBUG_LOG_ENV_VAR = "SERVE_DEBUG_LOG"

#: Logger used by serve components
SERVE_LOGGER_NAME = "ray.serve"

#: Actor name used to register controller
SERVE_CONTROLLER_NAME = "SERVE_CONTROLLER_ACTOR"

#: Actor name used to register HTTP proxy actor
SERVE_PROXY_NAME = "SERVE_PROXY_ACTOR"

#: Ray namespace used for all Serve actors
SERVE_NAMESPACE = "serve"

#: HTTP Address
DEFAULT_HTTP_ADDRESS = "http://127.0.0.1:8000"

#: HTTP Host
DEFAULT_HTTP_HOST = "127.0.0.1"

#: HTTP Port
DEFAULT_HTTP_PORT = 8000

#: gRPC Port
DEFAULT_GRPC_PORT = 9000

#: Default Serve application name
SERVE_DEFAULT_APP_NAME = "default"

#: Separator between app name and deployment name when we prepend
#: the app name to each deployment name. This prepending is currently
#: used to manage deployments from different applications holding the
#: same names.
DEPLOYMENT_NAME_PREFIX_SEPARATOR = "_"

#: Max concurrency
ASYNC_CONCURRENCY = int(1e6)

# How often to call the control loop on the controller.
CONTROL_LOOP_PERIOD_S = 0.1

#: Max time to wait for HTTP proxy in `serve.start()`.
HTTP_PROXY_TIMEOUT = 60

#: Max retry count for allowing failures in replica constructor.
#: If no replicas at target version is running by the time we're at
#: max construtor retry count, deploy() is considered failed.
#: By default we set threshold as min(num_replicas * 3, this value)
MAX_DEPLOYMENT_CONSTRUCTOR_RETRY_COUNT = 100

#: Default histogram buckets for latency tracker.
DEFAULT_LATENCY_BUCKET_MS = [
    1,
    2,
    5,
    10,
    20,
    50,
    100,
    200,
    300,
    400,
    500,
    1000,
    2000,
    # 5 seconds
    5000,
    # 10 seconds
    10000,
    # 60 seconds
    60000,
    # 2min
    120000,
    # 5 min
    300000,
    # 10 min
    600000,
]

#: Name of deployment health check method implemented by user.
HEALTH_CHECK_METHOD = "check_health"

#: Name of deployment reconfiguration method implemented by user.
RECONFIGURE_METHOD = "reconfigure"

SERVE_ROOT_URL_ENV_KEY = "RAY_SERVE_ROOT_URL"

#: Number of historically deleted deployments to store in the checkpoint.
MAX_NUM_DELETED_DEPLOYMENTS = 1000

#: Limit the number of cached handles because each handle has long poll
#: overhead. See https://github.com/ray-project/ray/issues/18980
MAX_CACHED_HANDLES = 100

#: Because ServeController will accept one long poll request per handle, its
#: concurrency needs to scale as O(num_handles)
CONTROLLER_MAX_CONCURRENCY = 15000

DEFAULT_GRACEFUL_SHUTDOWN_TIMEOUT_S = 20
DEFAULT_GRACEFUL_SHUTDOWN_WAIT_LOOP_S = 2
DEFAULT_HEALTH_CHECK_PERIOD_S = 10
DEFAULT_HEALTH_CHECK_TIMEOUT_S = 30
DEFAULT_MAX_CONCURRENT_QUERIES = 100

# HTTP Proxy health check period
PROXY_HEALTH_CHECK_PERIOD_S = (
    float(os.environ.get("RAY_SERVE_PROXY_HEALTH_CHECK_PERIOD_S", "10")) or 10
)
PROXY_READY_CHECK_TIMEOUT_S = (
    float(os.environ.get("RAY_SERVE_PROXY_READY_CHECK_TIMEOUT_S", "5")) or 5
)

#: Number of times in a row that a HTTP proxy must fail the health check before
#: being marked unhealthy.
PROXY_HEALTH_CHECK_UNHEALTHY_THRESHOLD = 3

#: Number of times in a row that a replica must fail the health check before
#: being marked unhealthy.
REPLICA_HEALTH_CHECK_UNHEALTHY_THRESHOLD = 3

# Key used to idenfity given json represents a serialized RayServeHandle
SERVE_HANDLE_JSON_KEY = "__SerializedServeHandle__"

# The time in seconds that the Serve client waits before rechecking deployment state
CLIENT_POLLING_INTERVAL_S: float = 1

# Handle metric push interval. (This interval will affect the cold start time period)
HANDLE_METRIC_PUSH_INTERVAL_S = 10

# Timeout for GCS internal KV service
RAY_SERVE_KV_TIMEOUT_S = float(os.environ.get("RAY_SERVE_KV_TIMEOUT_S", "0")) or None

# Timeout for GCS RPC request
RAY_GCS_RPC_TIMEOUT_S = 3.0

# Env var to control legacy sync deployment handle behavior in DAG.
SYNC_HANDLE_IN_DAG_FEATURE_FLAG_ENV_KEY = "SERVE_DEPLOYMENT_HANDLE_IS_SYNC"

# Maximum duration to wait until broadcasting a long poll update if there are
# still replicas in the RECOVERING state.
RECOVERING_LONG_POLL_BROADCAST_TIMEOUT_S = 10.0

# Minimum duration to wait until broadcasting model IDs.
PUSH_MULTIPLEXED_MODEL_IDS_INTERVAL_S = 1.0


class ServeHandleType(str, Enum):
    SYNC = "SYNC"
    ASYNC = "ASYNC"


# Deprecation message for V1 migrations.
MIGRATION_MESSAGE = (
    "See https://docs.ray.io/en/latest/serve/index.html for more information."
)


# [EXPERIMENTAL] Disable the http actor
SERVE_EXPERIMENTAL_DISABLE_HTTP_PROXY = "SERVE_EXPERIMENTAL_DISABLE_HTTP_PROXY"

# Message
MULTI_APP_MIGRATION_MESSAGE = (
    "Please see the documentation for ServeDeploySchema for more details on multi-app "
    "config files."
)

# Jsonify the log messages
RAY_SERVE_ENABLE_JSON_LOGGING = os.environ.get("RAY_SERVE_ENABLE_JSON_LOGGING") == "1"
# Logging format attributes
SERVE_LOG_REQUEST_ID = "request_id"
SERVE_LOG_ROUTE = "route"
SERVE_LOG_APPLICATION = "application"
SERVE_LOG_DEPLOYMENT = "deployment"
SERVE_LOG_REPLICA = "replica"
SERVE_LOG_COMPONENT = "component_name"
SERVE_LOG_COMPONENT_ID = "component_id"
SERVE_LOG_MESSAGE = "message"
# This is a reserved for python logging module attribute, it should not be changed.
SERVE_LOG_LEVEL_NAME = "levelname"
SERVE_LOG_TIME = "asctime"

# Logging format with record key to format string dict
SERVE_LOG_RECORD_FORMAT = {
    SERVE_LOG_REQUEST_ID: "%(request_id)s",
    SERVE_LOG_ROUTE: "%(route)s",
    SERVE_LOG_APPLICATION: "%(application)s",
    SERVE_LOG_MESSAGE: "%(filename)s:%(lineno)d - %(message)s",
    SERVE_LOG_LEVEL_NAME: "%(levelname)s",
    SERVE_LOG_TIME: "%(asctime)s",
}

# Serve HTTP request header key for routing requests.
SERVE_MULTIPLEXED_MODEL_ID = "serve_multiplexed_model_id"

# Feature flag to enable StreamingResponse support.
# When turned on, *all* HTTP responses will use Ray streaming object refs.
RAY_SERVE_ENABLE_EXPERIMENTAL_STREAMING = (
    os.environ.get("RAY_SERVE_ENABLE_EXPERIMENTAL_STREAMING", "0") == "1"
)
