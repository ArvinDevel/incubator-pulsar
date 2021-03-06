#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import traceback
import time
import util

from prometheus_client import Counter, Summary, Gauge

# We keep track of the following metrics
class Stats(object):
  metrics_label_names = ['tenant', 'namespace', 'function', 'instance_id', 'cluster']

  PULSAR_FUNCTION_METRICS_PREFIX = "pulsar_function_"
  USER_METRIC_PREFIX = "user_metric_";

  TOTAL_SUCCESSFULLY_PROCESSED = 'processed_successfully_total'
  TOTAL_SYSTEM_EXCEPTIONS = 'system_exceptions_total'
  TOTAL_USER_EXCEPTIONS = 'user_exceptions_total'
  PROCESS_LATENCY_MS = 'process_latency_ms'
  LAST_INVOCATION = 'last_invocation'
  TOTAL_RECEIVED = 'received_total'

  TOTAL_SUCCESSFULLY_PROCESSED_1min = 'processed_successfully_total_1min'
  TOTAL_SYSTEM_EXCEPTIONS_1min = 'system_exceptions_total_1min'
  TOTAL_USER_EXCEPTIONS_1min = 'user_exceptions_total_1min'
  PROCESS_LATENCY_MS_1min = 'process_latency_ms_1min'
  TOTAL_RECEIVED_1min = 'received_total_1min'

  # Declare Prometheus
  stat_total_processed_successfully = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_SUCCESSFULLY_PROCESSED,
                                              'Total number of messages processed successfully.', metrics_label_names)
  stat_total_sys_exceptions = Counter(PULSAR_FUNCTION_METRICS_PREFIX+ TOTAL_SYSTEM_EXCEPTIONS, 'Total number of system exceptions.',
                                      metrics_label_names)
  stat_total_user_exceptions = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_USER_EXCEPTIONS, 'Total number of user exceptions.',
                                       metrics_label_names)

  stat_process_latency_ms = Summary(PULSAR_FUNCTION_METRICS_PREFIX + PROCESS_LATENCY_MS, 'Process latency in milliseconds.', metrics_label_names)

  stat_last_invocation = Gauge(PULSAR_FUNCTION_METRICS_PREFIX + LAST_INVOCATION, 'The timestamp of the last invocation of the function.', metrics_label_names)

  stat_total_received = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_RECEIVED, 'Total number of messages received from source.', metrics_label_names)


  # 1min windowed metrics
  stat_total_processed_successfully_1min = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_SUCCESSFULLY_PROCESSED_1min,
                                              'Total number of messages processed successfully in the last 1 minute.', metrics_label_names)
  stat_total_sys_exceptions_1min = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_SYSTEM_EXCEPTIONS_1min,
                                      'Total number of system exceptions in the last 1 minute.',
                                      metrics_label_names)
  stat_total_user_exceptions_1min = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_USER_EXCEPTIONS_1min,
                                       'Total number of user exceptions in the last 1 minute.',
                                       metrics_label_names)

  stat_process_latency_ms_1min = Summary(PULSAR_FUNCTION_METRICS_PREFIX + PROCESS_LATENCY_MS_1min,
                                    'Process latency in milliseconds in the last 1 minute.', metrics_label_names)

  stat_total_received_1min = Counter(PULSAR_FUNCTION_METRICS_PREFIX + TOTAL_RECEIVED_1min,
                                'Total number of messages received from source in the last 1 minute.', metrics_label_names)

  latest_user_exception = []
  latest_sys_exception = []

  def __init__(self, metrics_labels):
    self.metrics_labels = metrics_labels;
    self.process_start_time = None

    # start time for windowed metrics
    util.FixedTimer(60, self.reset).start()

  def get_total_received(self):
    return self.stat_total_received.labels(*self.metrics_labels)._value.get();

  def get_total_processed_successfully(self):
    return self.stat_total_processed_successfully.labels(*self.metrics_labels)._value.get();

  def get_total_sys_exceptions(self):
    return self.stat_total_sys_exceptions.labels(*self.metrics_labels)._value.get();

  def get_total_user_exceptions(self):
    return self.stat_total_user_exceptions.labels(*self.metrics_labels)._value.get();

  def get_avg_process_latency(self):
    process_latency_ms_count = self.stat_process_latency_ms.labels(*self.metrics_labels)._count.get()
    process_latency_ms_sum = self.stat_process_latency_ms.labels(*self.metrics_labels)._sum.get()
    return 0.0 \
      if process_latency_ms_count <= 0.0 \
      else process_latency_ms_sum / process_latency_ms_count

  def get_total_processed_successfully_1min(self):
    return self.stat_total_processed_successfully_1min.labels(*self.metrics_labels)._value.get()

  def get_total_sys_exceptions_1min(self):
    return self.stat_total_sys_exceptions_1min.labels(*self.metrics_labels)._value.get()

  def get_total_user_exceptions_1min(self):
    return self.stat_total_user_exceptions_1min.labels(*self.metrics_labels)._value.get()

  def get_total_received_1min(self):
    return self.stat_total_received_1min.labels(*self.metrics_labels)._value.get()

  def get_avg_process_latency_1min(self):
    process_latency_ms_count = self.stat_process_latency_ms_1min.labels(*self.metrics_labels)._count.get()
    process_latency_ms_sum = self.stat_process_latency_ms_1min.labels(*self.metrics_labels)._sum.get()
    return 0.0 \
      if process_latency_ms_count <= 0.0 \
      else process_latency_ms_sum / process_latency_ms_count

  def get_last_invocation(self):
    return self.stat_last_invocation.labels(*self.metrics_labels)._value.get()

  def incr_total_processed_successfully(self):
    self.stat_total_processed_successfully.labels(*self.metrics_labels).inc()
    self.stat_total_processed_successfully_1min.labels(*self.metrics_labels).inc()

  def incr_total_sys_exceptions(self):
    self.stat_total_sys_exceptions.labels(*self.metrics_labels).inc()
    self.stat_total_sys_exceptions_1min.labels(*self.metrics_labels).inc()
    self.add_sys_exception()

  def incr_total_user_exceptions(self):
    self.stat_total_user_exceptions.labels(*self.metrics_labels).inc()
    self.stat_total_user_exceptions_1min.labels(*self.metrics_labels).inc()
    self.add_user_exception()

  def incr_total_received(self):
    self.stat_total_received.labels(*self.metrics_labels).inc()
    self.stat_total_received_1min.labels(*self.metrics_labels).inc()

  def process_time_start(self):
    self.process_start_time = time.time();

  def process_time_end(self):
    if self.process_start_time:
      duration = (time.time() - self.process_start_time) * 1000.0
      self.stat_process_latency_ms.labels(*self.metrics_labels).observe(duration)
      self.stat_process_latency_ms_1min.labels(*self.metrics_labels).observe(duration)

  def set_last_invocation(self, time):
    self.stat_last_invocation.labels(*self.metrics_labels).set(time * 1000.0)

  def add_user_exception(self):
    self.latest_sys_exception.append((traceback.format_exc(), int(time.time() * 1000)))
    if len(self.latest_sys_exception) > 10:
      self.latest_sys_exception.pop(0)

  def add_sys_exception(self):
    self.latest_sys_exception.append((traceback.format_exc(), int(time.time() * 1000)))
    if len(self.latest_sys_exception) > 10:
      self.latest_sys_exception.pop(0)

  def reset(self):
    self.latest_user_exception = []
    self.latest_sys_exception = []
    self.stat_total_processed_successfully_1min.labels(*self.metrics_labels)._value.set(0.0)
    self.stat_total_user_exceptions_1min.labels(*self.metrics_labels)._value.set(0.0)
    self.stat_total_sys_exceptions_1min.labels(*self.metrics_labels)._value.set(0.0)
    self.stat_process_latency_ms_1min.labels(*self.metrics_labels)._sum.set(0.0)
    self.stat_process_latency_ms_1min.labels(*self.metrics_labels)._count.set(0.0)
    self.stat_total_received_1min.labels(*self.metrics_labels)._value.set(0.0)