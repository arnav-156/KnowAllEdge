"""
Grafana Dashboard Configurations
Provides JSON configurations for Grafana dashboards

Requirements: 8.2, 8.5
"""

import json
from typing import Dict, Any, List


def create_system_metrics_dashboard() -> Dict[str, Any]:
    """
    Create Grafana dashboard for system metrics
    
    Panels:
    - CPU usage
    - Memory usage
    - Disk usage
    - Network I/O
    
    Returns:
        Grafana dashboard JSON configuration
    """
    return {
        "dashboard": {
            "title": "KnowAllEdge - System Metrics",
            "tags": ["KNOWALLEDGE", "system"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "CPU Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [{
                        "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                        "legendFormat": "CPU Usage %",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "percent",
                        "max": 100,
                        "min": 0
                    }]
                },
                {
                    "id": 2,
                    "title": "Memory Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [{
                        "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                        "legendFormat": "Memory Usage %",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "percent",
                        "max": 100,
                        "min": 0
                    }]
                },
                {
                    "id": 3,
                    "title": "Disk Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [{
                        "expr": "(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100",
                        "legendFormat": "Disk Usage %",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "percent",
                        "max": 100,
                        "min": 0
                    }]
                },
                {
                    "id": 4,
                    "title": "Network I/O",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "rate(node_network_receive_bytes_total[5m])",
                            "legendFormat": "Receive {{device}}",
                            "refId": "A"
                        },
                        {
                            "expr": "rate(node_network_transmit_bytes_total[5m])",
                            "legendFormat": "Transmit {{device}}",
                            "refId": "B"
                        }
                    ],
                    "yaxes": [{
                        "format": "Bps"
                    }]
                }
            ]
        }
    }


def create_application_metrics_dashboard() -> Dict[str, Any]:
    """
    Create Grafana dashboard for application metrics
    
    Panels:
    - Request rate
    - Response time (p50, p95, p99)
    - Error rate
    - Active requests
    - Database connections
    - Cache hit ratio
    
    Returns:
        Grafana dashboard JSON configuration
    
    Requirements: 8.2, 8.5
    """
    return {
        "dashboard": {
            "title": "KnowAllEdge - Application Metrics",
            "tags": ["KNOWALLEDGE", "application"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Request Rate",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [{
                        "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
                        "legendFormat": "{{endpoint}}",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "reqps",
                        "label": "Requests/sec"
                    }]
                },
                {
                    "id": 2,
                    "title": "Response Time",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                            "legendFormat": "p50",
                            "refId": "A"
                        },
                        {
                            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                            "legendFormat": "p95",
                            "refId": "B"
                        },
                        {
                            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                            "legendFormat": "p99",
                            "refId": "C"
                        }
                    ],
                    "yaxes": [{
                        "format": "s",
                        "label": "Duration"
                    }]
                },
                {
                    "id": 3,
                    "title": "Error Rate",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [{
                        "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
                        "legendFormat": "Error Rate %",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "percent",
                        "label": "Error %"
                    }],
                    "alert": {
                        "conditions": [{
                            "evaluator": {"params": [5], "type": "gt"},
                            "operator": {"type": "and"},
                            "query": {"params": ["A", "5m", "now"]},
                            "reducer": {"params": [], "type": "avg"},
                            "type": "query"
                        }],
                        "executionErrorState": "alerting",
                        "frequency": "1m",
                        "handler": 1,
                        "name": "High Error Rate",
                        "noDataState": "no_data",
                        "notifications": []
                    }
                },
                {
                    "id": 4,
                    "title": "Active Requests",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [{
                        "expr": "sum(http_requests_in_progress) by (endpoint)",
                        "legendFormat": "{{endpoint}}",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "short",
                        "label": "Requests"
                    }]
                },
                {
                    "id": 5,
                    "title": "Database Connections",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                    "targets": [
                        {
                            "expr": "db_pool_size",
                            "legendFormat": "Pool Size",
                            "refId": "A"
                        },
                        {
                            "expr": "db_connections_in_use",
                            "legendFormat": "In Use",
                            "refId": "B"
                        },
                        {
                            "expr": "db_pool_overflow",
                            "legendFormat": "Overflow",
                            "refId": "C"
                        }
                    ],
                    "yaxes": [{
                        "format": "short",
                        "label": "Connections"
                    }]
                },
                {
                    "id": 6,
                    "title": "Cache Hit Ratio",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                    "targets": [{
                        "expr": "cache_hit_rate",
                        "legendFormat": "Hit Rate %",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "percent",
                        "max": 100,
                        "min": 0,
                        "label": "Hit Rate"
                    }]
                }
            ]
        }
    }


def create_business_metrics_dashboard() -> Dict[str, Any]:
    """
    Create Grafana dashboard for business metrics
    
    Panels:
    - Subtopics generated
    - Explanations generated
    - Images generated
    - Gemini API calls
    - Token usage
    - API costs
    
    Returns:
        Grafana dashboard JSON configuration
    
    Requirements: 8.2, 8.5
    """
    return {
        "dashboard": {
            "title": "KnowAllEdge - Business Metrics",
            "tags": ["KNOWALLEDGE", "business"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Content Generation Rate",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": "rate(subtopics_generated_total[5m])",
                            "legendFormat": "Subtopics/sec",
                            "refId": "A"
                        },
                        {
                            "expr": "rate(explanations_generated_total[5m])",
                            "legendFormat": "Explanations/sec",
                            "refId": "B"
                        },
                        {
                            "expr": "rate(images_generated_total[5m])",
                            "legendFormat": "Images/sec",
                            "refId": "C"
                        }
                    ],
                    "yaxes": [{
                        "format": "ops",
                        "label": "Rate"
                    }]
                },
                {
                    "id": 2,
                    "title": "Gemini API Calls",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [{
                        "expr": "sum(rate(gemini_api_calls_total[5m])) by (model, status)",
                        "legendFormat": "{{model}} - {{status}}",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "ops",
                        "label": "Calls/sec"
                    }]
                },
                {
                    "id": 3,
                    "title": "Token Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [{
                        "expr": "sum(rate(gemini_api_tokens_total[5m])) by (model)",
                        "legendFormat": "{{model}}",
                        "refId": "A"
                    }],
                    "yaxes": [{
                        "format": "short",
                        "label": "Tokens/sec"
                    }]
                },
                {
                    "id": 4,
                    "title": "Quota Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "quota_requests_current_minute",
                            "legendFormat": "Requests (current minute)",
                            "refId": "A"
                        },
                        {
                            "expr": "quota_rpm_limit",
                            "legendFormat": "RPM Limit",
                            "refId": "B"
                        },
                        {
                            "expr": "quota_tokens_current_minute",
                            "legendFormat": "Tokens (current minute)",
                            "refId": "C"
                        },
                        {
                            "expr": "quota_tpm_limit",
                            "legendFormat": "TPM Limit",
                            "refId": "D"
                        }
                    ],
                    "yaxes": [{
                        "format": "short",
                        "label": "Count"
                    }]
                },
                {
                    "id": 5,
                    "title": "Circuit Breaker Status",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                    "targets": [{
                        "expr": "circuit_breaker_state",
                        "legendFormat": "{{service}}",
                        "refId": "A"
                    }],
                    "options": {
                        "colorMode": "background",
                        "graphMode": "none",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {
                            "calcs": ["lastNotNull"],
                            "fields": "",
                            "values": False
                        },
                        "textMode": "auto"
                    },
                    "fieldConfig": {
                        "defaults": {
                            "mappings": [
                                {"type": "value", "value": "0", "text": "Closed", "color": "green"},
                                {"type": "value", "value": "1", "text": "Open", "color": "red"},
                                {"type": "value", "value": "2", "text": "Half-Open", "color": "yellow"}
                            ],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"value": None, "color": "green"},
                                    {"value": 1, "color": "red"}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 6,
                    "title": "Content Quality Scores",
                    "type": "heatmap",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                    "targets": [{
                        "expr": "sum(rate(content_quality_score_bucket[5m])) by (le, content_type)",
                        "legendFormat": "{{content_type}}",
                        "refId": "A",
                        "format": "heatmap"
                    }],
                    "dataFormat": "tsbuckets"
                }
            ]
        }
    }


def export_dashboard_to_file(dashboard: Dict[str, Any], filename: str):
    """
    Export dashboard configuration to JSON file
    
    Args:
        dashboard: Dashboard configuration dictionary
        filename: Output filename
    """
    with open(filename, 'w') as f:
        json.dump(dashboard, f, indent=2)


def get_all_dashboards() -> List[Dict[str, Any]]:
    """
    Get all dashboard configurations
    
    Returns:
        List of dashboard configurations
    """
    return [
        create_system_metrics_dashboard(),
        create_application_metrics_dashboard(),
        create_business_metrics_dashboard()
    ]


# Example usage and documentation
DASHBOARD_SETUP_GUIDE = """
# Grafana Dashboard Setup Guide

## Prerequisites
- Grafana installed and running
- Prometheus data source configured in Grafana

## Import Dashboards

### Method 1: Via Grafana UI
1. Open Grafana (http://localhost:3000)
2. Navigate to Dashboards > Import
3. Copy the JSON from the dashboard configuration
4. Paste into the import dialog
5. Select Prometheus data source
6. Click Import

### Method 2: Via API
```bash
# Export dashboard to file
python -c "
from grafana_dashboards import create_application_metrics_dashboard, export_dashboard_to_file
dashboard = create_application_metrics_dashboard()
export_dashboard_to_file(dashboard, 'application_metrics.json')
"

# Import to Grafana
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \\
  -H "Content-Type: application/json" \\
  -d @application_metrics.json
```

### Method 3: Provisioning
1. Create provisioning directory: /etc/grafana/provisioning/dashboards/
2. Create dashboard provider config:

```yaml
# /etc/grafana/provisioning/dashboards/KNOWALLEDGE.yml
apiVersion: 1

providers:
  - name: 'KnowAllEdge'
    orgId: 1
    folder: 'KnowAllEdge'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards/KNOWALLEDGE
```

3. Place dashboard JSON files in /var/lib/grafana/dashboards/KNOWALLEDGE/
4. Restart Grafana

## Configure Alerts

### Email Notifications
1. Go to Alerting > Notification channels
2. Add new channel:
   - Type: Email
   - Addresses: your-email@example.com
3. Test notification

### Slack Notifications
1. Create Slack webhook URL
2. Add notification channel:
   - Type: Slack
   - Webhook URL: your-webhook-url
3. Test notification

### PagerDuty Notifications
1. Get PagerDuty integration key
2. Add notification channel:
   - Type: PagerDuty
   - Integration Key: your-key
3. Test notification

## Dashboard Variables

Add template variables for filtering:
- Environment: production, staging, development
- Instance: backend-1, backend-2, etc.
- Endpoint: /api/*, specific endpoints

## Useful Queries

### Error Rate by Endpoint
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint) 
/ 
sum(rate(http_requests_total[5m])) by (endpoint) * 100
```

### Slow Requests (>1s)
```promql
histogram_quantile(0.99, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
) > 1
```

### Database Connection Pool Saturation
```promql
db_connections_in_use / db_pool_size * 100
```

### Cache Effectiveness
```promql
sum(rate(cache_operations_total{result="hit"}[5m])) 
/ 
sum(rate(cache_operations_total[5m])) * 100
```
"""


if __name__ == "__main__":
    # Export all dashboards
    dashboards = get_all_dashboards()
    for i, dashboard in enumerate(dashboards):
        title = dashboard['dashboard']['title'].replace(' ', '_').lower()
        filename = f"{title}.json"
        export_dashboard_to_file(dashboard, filename)
        print(f"Exported: {filename}")
