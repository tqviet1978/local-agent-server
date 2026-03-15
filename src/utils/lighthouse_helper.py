"""
Lighthouse Helper - Utilities for Lighthouse operations
"""
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime


# Lighthouse presets
PRESETS = {
    "quick": {
        "categories": ["performance"],
        "throttling": {"network": "4g", "cpu_slowdown": 4},
        "only_audits": [
            "first-contentful-paint",
            "largest-contentful-paint",
            "speed-index",
            "total-blocking-time",
            "cumulative-layout-shift"
        ]
    },
    "ci": {
        "categories": ["performance", "accessibility", "best-practices", "seo"],
        "throttling": {"network": "4g", "cpu_slowdown": 4},
        "chrome_flags": ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]
    },
    "full": {
        "categories": ["performance", "accessibility", "best-practices", "seo", "pwa"],
        "throttling": {"network": "4g", "cpu_slowdown": 4}
    },
    "performance-only": {
        "categories": ["performance"],
        "throttling": {"network": "4g", "cpu_slowdown": 4}
    },
    "accessibility-only": {
        "categories": ["accessibility"],
        "throttling": None
    }
}


# Device presets
DEVICE_PRESETS = {
    "mobile": {
        "viewport_width": 412,
        "viewport_height": 823,
        "device_scale_factor": 2.625,
        "user_agent": "mobile"
    },
    "desktop": {
        "viewport_width": 1920,
        "viewport_height": 1080,
        "device_scale_factor": 1,
        "user_agent": "desktop"
    }
}


def check_lighthouse_installed():
    """Check if Lighthouse CLI is installed"""
    return shutil.which("lighthouse") is not None


def get_lighthouse_version():
    """Get installed Lighthouse version"""
    try:
        result = subprocess.run(
            ["lighthouse", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def build_lighthouse_command(url, options):
    """Build Lighthouse CLI command from options"""
    cmd = ["lighthouse", url]

    # Output formats
    output_formats = options.get("output", {}).get("formats", ["json", "html"])
    for fmt in output_formats:
        cmd.extend(["--output", fmt])

    # Output path
    output_path = options.get("output", {}).get("output_path")
    if output_path:
        cmd.extend(["--output-path", output_path])

    # Device/Form factor
    device = options.get("device", "mobile")
    if device == "mobile":
        cmd.extend(["--preset", "perf", "--form-factor", "mobile"])
    else:
        cmd.extend(["--form-factor", "desktop"])

    # Categories
    categories = options.get("categories", {})
    if isinstance(categories, dict):
        for cat, enabled in categories.items():
            if enabled:
                cmd.extend(["--only-categories", cat])
    elif isinstance(categories, list):
        for cat in categories:
            cmd.extend(["--only-categories", cat])

    # Throttling
    throttling = options.get("throttling", {})
    if throttling:
        throttling_method = throttling.get("method", "simulate")
        cmd.extend(["--throttling-method", throttling_method])

        if throttling.get("cpu_slowdown"):
            cmd.extend(["--throttling.cpuSlowdownMultiplier", str(throttling["cpu_slowdown"])])

    # Skip audits
    skip_audits = options.get("skip_audits", [])
    for audit in skip_audits:
        cmd.extend(["--skip-audits", audit])

    # Only audits
    only_audits = options.get("only_audits")
    if only_audits:
        for audit in only_audits:
            cmd.extend(["--only-audits", audit])

    # Extra headers
    extra_headers = options.get("extra_headers", {})
    if extra_headers:
        header_str = json.dumps(extra_headers)
        cmd.extend(["--extra-headers", header_str])

    # Chrome flags
    chrome_flags = options.get("chrome_flags", [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu"
    ])
    for flag in chrome_flags:
        cmd.extend(["--chrome-flags", flag])

    # Locale
    locale = options.get("locale")
    if locale:
        cmd.extend(["--locale", locale])

    # Max wait time
    max_wait = options.get("max_wait_for_load")
    if max_wait:
        cmd.extend(["--max-wait-for-load", str(max_wait)])

    # Budget path (if provided)
    budget_path = options.get("budget_path")
    if budget_path:
        cmd.extend(["--budget-path", budget_path])

    return cmd


def run_lighthouse(url, options, working_dir=None):
    """
    Run Lighthouse audit

    Args:
        url: URL to audit
        options: Lighthouse options dict
        working_dir: Working directory for output files

    Returns:
        dict with audit results
    """
    if not check_lighthouse_installed():
        raise Exception("Lighthouse is not installed. Run setup_lighthouse.sh first.")

    # Apply preset if specified
    preset = options.get("preset")
    if preset and preset in PRESETS:
        preset_config = PRESETS[preset].copy()
        # Merge preset with user options (user options take precedence)
        for key, value in preset_config.items():
            if key not in options:
                options[key] = value

    # Build command
    cmd = build_lighthouse_command(url, options)

    # Wrap with xvfb-run if available (for headless Chrome on servers without X)
    if shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24"] + cmd

    # Run Lighthouse
    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=options.get("timeout", 120)
        )

        if result.returncode != 0:
            raise Exception(f"Lighthouse failed: {result.stderr}")

        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        raise Exception("Lighthouse audit timed out")
    except Exception as e:
        raise Exception(f"Failed to run Lighthouse: {str(e)}")


def parse_lighthouse_json(json_path):
    """Parse Lighthouse JSON report and extract key metrics"""
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Extract scores
    categories = data.get("categories", {})
    scores = {
        cat_id: cat_data.get("score", 0)
        for cat_id, cat_data in categories.items()
    }

    # Extract metrics
    audits = data.get("audits", {})
    metrics = {}

    metric_mapping = {
        "first-contentful-paint": "first_contentful_paint",
        "largest-contentful-paint": "largest_contentful_paint",
        "speed-index": "speed_index",
        "interactive": "time_to_interactive",
        "total-blocking-time": "total_blocking_time",
        "cumulative-layout-shift": "cumulative_layout_shift"
    }

    for audit_id, metric_key in metric_mapping.items():
        if audit_id in audits:
            audit_data = audits[audit_id]
            if "numericValue" in audit_data:
                metrics[metric_key] = int(audit_data["numericValue"])
            elif "displayValue" in audit_data:
                metrics[metric_key] = audit_data["displayValue"]

    # Extract opportunities (performance improvements)
    opportunities = []
    for audit_id, audit_data in audits.items():
        if audit_data.get("details", {}).get("type") == "opportunity":
            opportunities.append({
                "id": audit_id,
                "title": audit_data.get("title", ""),
                "score": audit_data.get("score"),
                "savings_ms": audit_data.get("details", {}).get("overallSavingsMs", 0),
                "savings_bytes": audit_data.get("details", {}).get("overallSavingsBytes", 0)
            })

    # Sort by savings
    opportunities.sort(key=lambda x: x.get("savings_ms", 0), reverse=True)

    # Extract diagnostics
    diagnostics = []
    for audit_id, audit_data in audits.items():
        if (audit_data.get("details", {}).get("type") == "diagnostic" or
            audit_data.get("scoreDisplayMode") == "informative"):
            if audit_data.get("score") is not None and audit_data.get("score") < 1:
                diagnostics.append({
                    "id": audit_id,
                    "title": audit_data.get("title", ""),
                    "score": audit_data.get("score"),
                    "description": audit_data.get("description", "")
                })

    # Count passed/failed audits
    passed_audits = sum(1 for a in audits.values() if a.get("score") == 1)
    failed_audits = sum(1 for a in audits.values() if a.get("score") is not None and a.get("score") < 1)
    total_audits = len([a for a in audits.values() if a.get("score") is not None])

    return {
        "url": data.get("finalDisplayedUrl", ""),
        "fetch_time": data.get("fetchTime", ""),
        "lighthouse_version": data.get("lighthouseVersion", ""),
        "scores": scores,
        "metrics": metrics,
        "opportunities": opportunities[:10],  # Top 10
        "diagnostics": diagnostics[:10],  # Top 10
        "passed_audits": passed_audits,
        "failed_audits": failed_audits,
        "total_audits": total_audits
    }


def check_budget_violations(parsed_report, budgets):
    """Check if metrics violate performance budgets"""
    violations = []

    if not budgets:
        return violations

    # Check performance budgets
    perf_budgets = budgets.get("performance", {})
    metrics = parsed_report.get("metrics", {})

    metric_mapping = {
        "fcp": "first_contentful_paint",
        "lcp": "largest_contentful_paint",
        "tti": "time_to_interactive",
        "tbt": "total_blocking_time",
        "cls": "cumulative_layout_shift",
        "speed_index": "speed_index"
    }

    for budget_key, budget_value in perf_budgets.items():
        metric_key = metric_mapping.get(budget_key)
        if metric_key and metric_key in metrics:
            actual = metrics[metric_key]
            if actual > budget_value:
                violations.append({
                    "metric": budget_key,
                    "budget": budget_value,
                    "actual": actual,
                    "over_budget": actual - budget_value
                })

    return violations


def generate_timestamp_filename(prefix="audit"):
    """Generate timestamped filename"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{timestamp}"