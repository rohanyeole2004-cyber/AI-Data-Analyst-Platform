def configure_monitoring(connection_string=None):
 if not connection_string:return
 from azure.monitor.opentelemetry import configure_azure_monitor
 configure_azure_monitor(connection_string=connection_string)
