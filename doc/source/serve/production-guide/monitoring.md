(serve-monitoring)=

# Monitoring Ray Serve

This section helps you debug and monitor your Serve applications by:

* viewing the Ray dashboard
* using Ray logging and Loki
* inspecting built-in Ray Serve metrics
* exporting metrics into Arize platform

## Ray dashboard

You can use the Ray dashboard to get a high-level overview of your Ray cluster and Ray Serve application's states.
This includes details such as:
* the number of deployment replicas currently running
* logs for your Serve controller, deployment replicas, and HTTP proxies
* the Ray nodes (i.e. machines) running in your Ray cluster.

You can access the Ray dashboard at port 8265 at your cluster's URI.
For example, if you're running Ray Serve locally, you can access the dashboard by going to `http://localhost:8265` in your browser.

View important information about your application by accessing the [Serve page](dash-serve-view).

```{image} https://raw.githubusercontent.com/ray-project/Images/master/docs/new-dashboard-v2/serve.png
:align: center
```

This example has a single-node cluster running a deployment named `Translator`. This deployment has 2 replicas.

View details of these replicas by browsing the Serve page. On the details page of each replica. From there, you can view metadata about the replica and the logs of the replicas, including the `logging` and `print` statements generated by the replica process.


Another useful view is the [Actors view](dash-actors-view). This example Serve application uses four [Ray actors](actor-guide):

- 1 Serve controller
- 1 HTTP proxy
- 2 `Translator` deployment replicas

You can see the details of these entities throughout the Serve page and in the actor's page.
This page includes additional useful information like each actor's process ID (PID) and a link to each actor's logs. You can also see whether any particular actor is alive or dead to help you debug potential cluster failures.

:::{tip}
To learn more about the Serve controller actor, the HTTP proxy actor(s), the deployment replicas, and how they all work together, check out the [Serve Architecture](serve-architecture) documentation.
:::

For a detailed overview of the Ray dashboard, see the [dashboard documentation](observability-getting-started).

## Ray logging

To understand system-level behavior and to surface application-level details during runtime, you can leverage Ray logging.

Ray Serve uses Python's standard `logging` module with a logger named `"ray.serve"`.
By default, logs are emitted from actors both to `stderr` and on disk on each node at `/tmp/ray/session_latest/logs/serve/`.
This includes both system-level logs from the Serve controller and HTTP proxy as well as access logs and custom user logs produced from within deployment replicas.

In development, logs are streamed to the driver Ray program (the Python script that calls `serve.run()` or the `serve run` CLI command), so it's convenient to keep the driver running while debugging.

For example, let's run a basic Serve application and view the logs that it emits.

First, let's create a simple deployment that logs a custom log message when it's queried:

```{literalinclude} ../doc_code/monitoring/monitoring.py
:start-after: __start__
:end-before: __end__
:language: python
```

Run this deployment using the `serve run` CLI command:

```console
$ serve run monitoring:say_hello

2023-04-10 15:57:32,100	INFO scripts.py:380 -- Deploying from import path: "monitoring:say_hello".
[2023-04-10 15:57:33]  INFO ray._private.worker::Started a local Ray instance. View the dashboard at http://127.0.0.1:8265 
(ServeController pid=63503) INFO 2023-04-10 15:57:35,822 controller 63503 deployment_state.py:1168 - Deploying new version of deployment SayHello.
(HTTPProxyActor pid=63513) INFO:     Started server process [63513]
(ServeController pid=63503) INFO 2023-04-10 15:57:35,882 controller 63503 deployment_state.py:1386 - Adding 1 replica to deployment SayHello.
2023-04-10 15:57:36,840	SUCC scripts.py:398 -- Deployed Serve app successfully.
```

`serve run` prints a few log messages immediately. Note that a few of these messages start with identifiers such as

```
(ServeController pid=63881)
```

These messages are logs from Ray Serve [actors](actor-guide). They describe which actor (Serve controller, HTTP proxy, or deployment replica) created the log and what its process ID is (which is useful when distinguishing between different deployment replicas or HTTP proxies). The rest of these log messages are the actual log statements generated by the actor.

While `serve run` is running, we can query the deployment in a separate terminal window:

```
curl -X GET http://localhost:8000/
```

This causes the HTTP proxy and deployment replica to print log statements to the terminal running `serve run`:

```console
(ServeReplica:SayHello pid=63520) INFO 2023-04-10 15:59:45,403 SayHello SayHello#kTBlTj HzIYOzaEgN / monitoring.py:16 - Hello world!
(ServeReplica:SayHello pid=63520) INFO 2023-04-10 15:59:45,403 SayHello SayHello#kTBlTj HzIYOzaEgN / replica.py:527 - __CALL__ OK 0.5ms
```

:::{note}
Log messages include the logging level, timestamp, deployment name, replica tag, request ID, route, file name, and line number.
:::

Find a copy of these logs at `/tmp/ray/session_latest/logs/serve/`. You can parse these stored logs with a logging stack such as ELK or [Loki](serve-logging-loki) to be able to search by deployment or replica.

Serve supports [Log Rotation](log-rotation) of these logs through setting the environment variables `RAY_ROTATION_MAX_BYTES` and `RAY_ROTATION_BACKUP_COUNT`.

To silence the replica-level logs or otherwise configure logging, configure the `"ray.serve"` logger **inside the deployment constructor**:

```python
import logging

logger = logging.getLogger("ray.serve")

@serve.deployment
class Silenced:
    def __init__(self):
        logger.setLevel(logging.ERROR)
```

This controls which logs are written to STDOUT or files on disk.
In addition to the standard Python logger, Serve supports custom logging. Custom logging lets you control what messages are written to STDOUT/STDERR, files on disk, or both.

For a detailed overview of logging in Ray, see [Ray Logging](configure-logging).

(serve-logging-loki)=
### Filtering logs with Loki

You can explore and filter your logs using [Loki](https://grafana.com/oss/loki/).
Setup and configuration are straightforward on Kubernetes, but as a tutorial, let's set up Loki manually.

For this walkthrough, you need both Loki and Promtail, which are both supported by [Grafana Labs](https://grafana.com). Follow the installation instructions at Grafana's website to get executables for [Loki](https://grafana.com/docs/loki/latest/installation/) and [Promtail](https://grafana.com/docs/loki/latest/clients/promtail/).
For convenience, save the Loki and Promtail executables in the same directory, and then navigate to this directory in your terminal.

Now let's get your logs into Loki using Promtail.

Save the following file as `promtail-local-config.yaml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: ray
    static_configs:
      - labels:
        job: ray
        __path__: /tmp/ray/session_latest/logs/serve/*.*
```

The relevant part for Ray Serve is the `static_configs` field, where we have indicated the location of our log files with `__path__`.
The expression `*.*` will match all files, but it won't match directories since they cause an error with Promtail.

We'll run Loki locally.  Grab the default config file for Loki with the following command in your terminal:

```shell
wget https://raw.githubusercontent.com/grafana/loki/v2.1.0/cmd/loki/loki-local-config.yaml
```

Now start Loki:

```shell
./loki-darwin-amd64 -config.file=loki-local-config.yaml
```

Here you may need to replace `./loki-darwin-amd64` with the path to your Loki executable file, which may have a different name depending on your operating system.

Start Promtail and pass in the path to the config file we saved earlier:

```shell
./promtail-darwin-amd64 -config.file=promtail-local-config.yaml
```

Once again, you may need to replace `./promtail-darwin-amd64` with your Promtail executable.

Run the following Python script to deploy a basic Serve deployment with a Serve deployment logger and to make some requests:

```{literalinclude} ../doc_code/monitoring/deployment_logger.py
:start-after: __start__
:end-before: __end__
:language: python
```

Now [install and run Grafana](https://grafana.com/docs/grafana/latest/installation/) and navigate to `http://localhost:3000`, where you can log in with default credentials:

* Username: admin
* Password: admin

On the welcome page, click "Add your first data source" and click "Loki" to add Loki as a data source.

Now click "Explore" in the left-side panel.  You are ready to run some queries!

To filter all these Ray logs for the ones relevant to our deployment, use the following [LogQL](https://grafana.com/docs/loki/latest/logql/) query:

```shell
{job="ray"} |= "Counter"
```

You should see something similar to the following:

```{image} https://raw.githubusercontent.com/ray-project/Images/master/docs/serve/loki-serve.png
:align: center
```

You can use Loki to filter your Ray Serve logs and gather insights quicker.

(serve-production-monitoring-metrics)=

## Built-in Ray Serve metrics

You can leverage built-in Ray Serve metrics to get a closer look at your application's performance.

Ray Serve exposes important system metrics like the number of successful and
failed requests through the [Ray metrics monitoring infrastructure](dash-metrics-view). By default, the metrics are exposed in Prometheus format on each node.

:::{note}
Different metrics are collected when Deployments are called
via Python `ServeHandle` and when they are called via HTTP.

See the list of metrics below marked for each.
:::

The following metrics are exposed by Ray Serve:

```{eval-rst}
.. list-table::
   :header-rows: 1

   * - Name
     - Fields
     - Description
   * - ``serve_deployment_request_counter`` [**]
     - * deployment
       * replica
       * route
       * application
     - The number of queries that have been processed in this replica.
   * - ``serve_deployment_error_counter`` [**]
     - * deployment
       * replica
       * route
       * application
     - The number of exceptions that have occurred in the deployment.
   * - ``serve_deployment_replica_starts`` [**]
     - * deployment
       * replica
       * application
     - The number of times this replica has been restarted due to failure.
   * - ``serve_deployment_replica_healthy``
     - * deployment
       * replica
       * application
     - Whether this deployment replica is healthy. 1 means healthy, 0 unhealthy.
   * - ``serve_deployment_processing_latency_ms`` [**]
     - * deployment
       * replica
       * route
       * application
     - The latency for queries to be processed.
   * - ``serve_replica_processing_queries`` [**]
     - * deployment
       * replica
       * application
     - The current number of queries being processed.
   * - ``serve_replica_pending_queries`` [**]
     - * deployment
       * replica
       * application
     - The current number of pending queries.
   * - ``serve_num_http_requests`` [*]
     - * route
       * method
       * application
     - The number of HTTP requests processed.
   * - ``serve_num_http_error_requests`` [*]
     - * route
       * error_code
       * method
     - The number of non-200 HTTP responses.
   * - ``serve_num_router_requests`` [*]
     - * deployment
       * route
       * application
     - The number of requests processed by the router.
   * - ``serve_handle_request_counter`` [**]
     - * handle
       * deployment
       * route
       * application
     - The number of requests processed by this ServeHandle.
   * - ``serve_deployment_queued_queries`` [*]
     - * deployment
       * route
     - The number of queries for this deployment waiting to be assigned to a replica.
   * - ``serve_num_deployment_http_error_requests`` [*]
     - * deployment
       * error_code
       * method
       * route
       * application
     - The number of non-200 HTTP responses returned by each deployment.
   * - ``serve_http_request_latency_ms`` [*]
     - * route
       * application
     - The end-to-end latency of HTTP requests (measured from the Serve HTTP proxy).
   * - ``serve_multiplexed_model_load_latency_s``
     - * deployment
       * replica
       * application
     - The time it takes to load a model.
   * - ``serve_multiplexed_model_unload_latency_s``
     - * deployment
       * replica
       * application
     - The time it takes to unload a model.
   * - ``serve_num_multiplexed_models``
     - * deployment
       * replica
       * application
     - The number of models loaded on the current replica.
   * - ``serve_multiplexed_models_unload_counter``
     - * deployment
       * replica
       * application
     - The number of times models unloaded on the current replica.
   * - ``serve_multiplexed_models_load_counter``
     - * deployment
       * replica
       * application
     - The number of times models loaded on the current replica.
```
[*] - only available when using HTTP calls
[**] - only available when using Python `ServeHandle` calls

To see this in action, first run the following command to start Ray and set up the metrics export port:

```bash
ray start --head --metrics-export-port=8080
```

Then run the following script:

```{literalinclude} ../doc_code/monitoring/metrics_snippet.py
:start-after: __start__
:end-before: __end__
:language: python
```

The requests loop until canceled with `Control-C`.

While this script is running, go to `localhost:8080` in your web browser.
In the output there, you can search for `serve_` to locate the metrics above.
The metrics are updated once every ten seconds, so you need to refresh the page to see new values.

For example, after running the script for some time and refreshing `localhost:8080` you should find metrics similar to the following:

```
ray_serve_deployment_processing_latency_ms_count{..., replica="sleeper#jtzqhX"} 48.0
ray_serve_deployment_processing_latency_ms_sum{..., replica="sleeper#jtzqhX"} 48160.6719493866
```

which indicates that the average processing latency is just over one second, as expected.

You can even define a [custom metric](application-level-metrics) for your deployment and tag it with deployment or replica metadata.
Here's an example:

```{literalinclude} ../doc_code/monitoring/custom_metric_snippet.py
:start-after: __start__
:end-before: __end__
```

The emitted logs include:

```
# HELP ray_my_counter The number of odd-numbered requests to this deployment.
# TYPE ray_my_counter gauge
ray_my_counter{..., deployment="MyDeployment",model="123",replica="MyDeployment#rUVqKh"} 5.0
```

See the [Ray Metrics documentation](collect-metrics) for more details, including instructions for scraping these metrics using Prometheus.

## Exporting metrics into Arize
Besides using Prometheus to check out Ray metrics, Ray Serve also has the flexibility to export the metrics into other observability platforms.

[Arize](https://docs.arize.com/arize/) is a machine learning observability platform which can help you to monitor real-time model performance, root cause model failures/performance degradation using explainability & slice analysis and surface drift, data quality, data consistency issues etc.

To integrate with Arize, add Arize client code directly into your Serve deployment code. ([Example code](https://docs.arize.com/arize/integrations/integrations/anyscale-ray-serve))
