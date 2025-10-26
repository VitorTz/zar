from fastapi.responses import HTMLResponse, JSONResponse
from src.perf.system_monitor import get_monitor
from src.schemas.reports import SystemReport
from datetime import datetime, timezone


def generate_analysis(memory_info: dict, cpu_info: dict, process_info: dict) -> dict:
    """Gera análise das métricas e recomendações"""
    
    # Análise de memória
    memory_percent = memory_info.get("process", {}).get("percent", 0)
    memory_mb = memory_info.get("process", {}).get("rss_mb", 0)
    
    if memory_percent > 80:
        memory_status = "critical"
        memory_level = "high"
        memory_details = f"Memory usage is critically high at {memory_percent}%"
    elif memory_percent > 60:
        memory_status = "warning"
        memory_level = "moderate"
        memory_details = f"Memory usage is moderate at {memory_percent}%"
    else:
        memory_status = "healthy"
        memory_level = "low"
        memory_details = f"Memory usage is healthy at {memory_percent}%"
    
    # Análise de CPU
    cpu_percent = cpu_info.get("process", {}).get("percent", 0)
    
    if cpu_percent > 80:
        cpu_status = "critical"
        cpu_level = "high"
        cpu_details = f"CPU usage is critically high at {cpu_percent}%"
    elif cpu_percent > 60:
        cpu_status = "warning"
        cpu_level = "moderate"
        cpu_details = f"CPU usage is moderate at {cpu_percent}%"
    else:
        cpu_status = "healthy"
        cpu_level = "low"
        cpu_details = f"CPU usage is healthy at {cpu_percent}%"
    
    # Status geral de saúde
    if memory_status == "critical" or cpu_status == "critical":
        health_status = "critical"
    elif memory_status == "warning" or cpu_status == "warning":
        health_status = "warning"
    else:
        health_status = "healthy"
    
    # Score geral (0-100)
    memory_score = max(0, 100 - memory_percent)
    cpu_score = max(0, 100 - cpu_percent)
    overall_score = int((memory_score + cpu_score) / 2)
    
    # Key findings
    key_findings = []
    requests = process_info.get("requests", {})
    
    key_findings.append(f"Application uptime: {process_info.get('uptime_formatted', 'N/A')}")
    key_findings.append(f"Total requests processed: {requests.get('total', 0):,}")
    key_findings.append(f"Memory usage: {memory_mb:.2f} MB ({memory_percent}%)")
    key_findings.append(f"CPU usage: {cpu_percent}%")
    
    if requests.get("error_rate_percent", 0) > 5:
        key_findings.append(f"⚠️ High error rate: {requests.get('error_rate_percent', 0)}%")
    
    # Recomendações
    recommendations = []
    
    if memory_percent > 70:
        recommendations.append("Consider increasing memory allocation or optimizing memory usage")
    
    if cpu_percent > 70:
        recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
    
    if requests.get("error_rate_percent", 0) > 5:
        recommendations.append("Investigate and fix the cause of high error rate")
    
    avg_response_time = process_info.get("response_time_stats", {}).get("avg", 0)
    if avg_response_time > 1000:
        recommendations.append(f"Average response time is high ({avg_response_time:.0f}ms), consider optimization")
    
    if not recommendations:
        recommendations.append("System is running optimally")
    
    return {
        "health_status": health_status,
        "overall_score": overall_score,
        "memory_status": memory_status,
        "memory_usage_level": memory_level,
        "memory_details": memory_details,
        "cpu_status": cpu_status,
        "cpu_usage_level": cpu_level,
        "cpu_details": cpu_details,
        "key_findings": key_findings,
        "recommendations": recommendations
    }


def calculate_network_error_rate(network_info: dict) -> float:
    """Calcula taxa de erro de rede"""
    io = network_info.get("io", {})
    total_packets = io.get("packets_sent", 0) + io.get("packets_recv", 0)
    total_errors = io.get("errors_in", 0) + io.get("errors_out", 0)
    
    if total_packets == 0:
        return 0.0
    
    return round((total_errors / total_packets) * 100, 2)


async def reset_metrics():
    monitor = get_monitor()
    monitor.reset_counters()
    return {"message": "Metrics counters reset successfully"}


async def clear_metrics():
    monitor = get_monitor()
    monitor.clear_history()
    return {"message": "Metrics history cleared successfully"}


async def generate_full_report() -> SystemReport:
    monitor = get_monitor()
        
    process_info = monitor.get_process_info()
    memory_info = monitor.get_memory_info()
    cpu_info = monitor.get_cpu_info()
    disk_info = monitor.get_disk_info()
    network_info = monitor.get_network_info()
    history = monitor.get_history(metric="all")    
    analysis = generate_analysis(memory_info, cpu_info, process_info)
    
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_period": {
            "uptime": process_info.get("uptime_formatted", "N/A"),
            "uptime_seconds": process_info.get("uptime_seconds", 0)
        },
        
        "executive_summary": {
            "health_status": analysis["health_status"],
            "overall_score": analysis["overall_score"],
            "key_findings": analysis["key_findings"],
            "recommendations": analysis["recommendations"]
        },
        
        "process_metrics": {
            "identification": {
                "pid": process_info.get("pid"),
                "name": process_info.get("name"),
                "status": process_info.get("status"),
                "threads": process_info.get("threads"),
                "file_descriptors": process_info.get("file_descriptors")
            },
            "uptime": {
                "seconds": process_info.get("uptime_seconds"),
                "formatted": process_info.get("uptime_formatted"),
                "started_at": process_info.get("created")
            },
            "requests": process_info.get("requests", {}),
            "response_times": process_info.get("response_time_stats", {})
        },
        
        "memory_metrics": {
            "process": memory_info.get("process", {}),
            "system": memory_info.get("system", {}),
            "python": memory_info.get("python", {}),
            "trends": memory_info.get("history_stats", {}),
            "analysis": {
                "status": analysis["memory_status"],
                "usage_level": analysis["memory_usage_level"],
                "details": analysis["memory_details"]
            }
        },
        
        "cpu_metrics": {
            "process": cpu_info.get("process", {}),
            "system": cpu_info.get("system", {}),
            "trends": cpu_info.get("history_stats", {}),
            "analysis": {
                "status": analysis["cpu_status"],
                "usage_level": analysis["cpu_usage_level"],
                "details": analysis["cpu_details"]
            }
        },
        
        "disk_metrics": {
            "usage": disk_info.get("usage", {}),
            "io": disk_info.get("io", {}),
            "analysis": {
                "status": "healthy" if disk_info.get("usage", {}).get("percent", 0) < 90 else "warning",
                "free_space_gb": disk_info.get("usage", {}).get("free_gb", 0)
            }
        },
        
        "network_metrics": {
            "io": network_info.get("io", {}),
            "connections": network_info.get("connections", {}),
            "analysis": {
                "total_traffic_mb": round(
                    network_info.get("io", {}).get("bytes_sent_mb", 0) + 
                    network_info.get("io", {}).get("bytes_recv_mb", 0), 2
                ),
                "error_rate": calculate_network_error_rate(network_info)
            }
        },
        
        "historical_data": {
            "memory": history.get("memory", []),
            "cpu": history.get("cpu", []),
            "response_time": history.get("response_time", [])
        },
        
        "metadata": {
            "monitoring_interval_seconds": 300,
            "history_size": len(history.get("memory", [])),
            "cache_ttl_seconds": 1.0
        }
    }
    
    return SystemReport(**report)


async def generate_metric_html_report():
    report: SystemReport = await generate_full_report()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Monitor Report</title>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
                margin-bottom: 15px;
                padding: 10px;
                background: #ecf0f1;
                border-left: 4px solid #3498db;
            }}
            .status {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            .status.healthy {{ background: #2ecc71; color: white; }}
            .status.warning {{ background: #f39c12; color: white; }}
            .status.critical {{ background: #e74c3c; color: white; }}
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }}
            .metric-card h3 {{
                color: #495057;
                font-size: 14px;
                margin-bottom: 10px;
                text-transform: uppercase;
            }}
            .metric-value {{
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .metric-unit {{
                font-size: 14px;
                color: #7f8c8d;
                margin-left: 5px;
            }}
            .info-list {{
                list-style: none;
                padding: 10px 0;
            }}
            .info-list li {{
                padding: 8px 0;
                border-bottom: 1px solid #ecf0f1;
            }}
            .info-list li:last-child {{ border-bottom: none; }}
            .label {{ font-weight: bold; color: #7f8c8d; }}
            .timestamp {{
                color: #95a5a6;
                font-size: 14px;
                margin-top: 30px;
                text-align: center;
            }}
            .recommendations {{
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }}
            .recommendations ul {{
                margin-left: 20px;
                margin-top: 10px;
            }}
            .score {{
                font-size: 48px;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
            }}
            .score.high {{ color: #2ecc71; }}
            .score.medium {{ color: #f39c12; }}
            .score.low {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 System Monitor Report</h1>
            
            <div style="text-align: center; margin: 30px 0;">
                <div class="status {report.executive_summary.health_status.lower()}">
                    {report.executive_summary.health_status.upper()}
                </div>
                <div class="score {'high' if report.executive_summary.overall_score >= 80 else 'medium' if report.executive_summary.overall_score >= 60 else 'low'}">
                    {report.executive_summary.overall_score}/100
                </div>
                <p style="color: #7f8c8d;">Overall Health Score</p>
            </div>
            
            <h2>🎯 Executive Summary</h2>
            <div class="recommendations">
                <h3 style="margin-bottom: 10px;">Key Findings:</h3>
                <ul>
                    {"".join(f"<li>{finding}</li>" for finding in report.executive_summary.key_findings)}
                </ul>
                
                {f'''<h3 style="margin-top: 15px; margin-bottom: 10px;">Recommendations:</h3>
                <ul>
                    {"".join(f"<li>{rec}</li>" for rec in report.executive_summary.recommendations)}
                </ul>''' if report.executive_summary.recommendations else ''}
            </div>
            
            <h2>⚡ Process Metrics</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h3>Uptime</h3>
                    <div class="metric-value">
                        {report.process_metrics.uptime.formatted}
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Total Requests</h3>
                    <div class="metric-value">
                        {report.process_metrics.requests.total:,}
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Error Rate</h3>
                    <div class="metric-value">
                        {report.process_metrics.requests.error_rate_percent}<span class="metric-unit">%</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Avg Response Time</h3>
                    <div class="metric-value">
                        {report.process_metrics.response_times.avg}<span class="metric-unit">ms</span>
                    </div>
                </div>
            </div>
            
            <h2>💾 Memory Metrics</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h3>Process Memory</h3>
                    <div class="metric-value">
                        {report.memory_metrics.process.rss_mb}<span class="metric-unit">MB</span>
                    </div>
                    <p style="margin-top: 10px; color: #7f8c8d; font-size: 14px;">
                        {report.memory_metrics.process.percent}% of system
                    </p>
                </div>
                <div class="metric-card">
                    <h3>Peak Memory</h3>
                    <div class="metric-value">
                        {report.memory_metrics.process.peak_mb}<span class="metric-unit">MB</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>System Available</h3>
                    <div class="metric-value">
                        {report.memory_metrics.system.available_mb}<span class="metric-unit">MB</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Python Objects</h3>
                    <div class="metric-value">
                        {report.memory_metrics.python.objects_count:,}
                    </div>
                </div>
            </div>
            
            <h2>🔥 CPU Metrics</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h3>Process CPU</h3>
                    <div class="metric-value">
                        {report.cpu_metrics.process.percent}<span class="metric-unit">%</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Peak CPU</h3>
                    <div class="metric-value">
                        {report.cpu_metrics.process.peak_percent}<span class="metric-unit">%</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>System CPU</h3>
                    <div class="metric-value">
                        {report.cpu_metrics.system.percent_total}<span class="metric-unit">%</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Threads</h3>
                    <div class="metric-value">
                        {report.cpu_metrics.process.num_threads}
                    </div>
                </div>
            </div>
            
            <h2>💿 Disk & Network</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h3>Disk Usage</h3>
                    <div class="metric-value">
                        {report.disk_metrics.usage.percent}<span class="metric-unit">%</span>
                    </div>
                    <p style="margin-top: 10px; color: #7f8c8d; font-size: 14px;">
                        {report.disk_metrics.usage.free_gb} GB free
                    </p>
                </div>
                <div class="metric-card">
                    <h3>Network Traffic</h3>
                    <div class="metric-value">
                        {report.network_metrics.analysis.total_traffic_mb}<span class="metric-unit">MB</span>
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Active Connections</h3>
                    <div class="metric-value">
                        {report.network_metrics.connections.active}
                    </div>
                </div>
                <div class="metric-card">
                    <h3>Network Errors</h3>
                    <div class="metric-value">
                        {report.network_metrics.analysis.error_rate}<span class="metric-unit">%</span>
                    </div>
                </div>
            </div>
            
            <div class="timestamp">
                Generated at: {report.generated_at}<br>
                Monitoring interval: {report.metadata.monitoring_interval_seconds}s | 
                History points: {report.metadata.history_size}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)