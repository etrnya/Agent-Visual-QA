import os
import sys
import json
import shutil
import argparse
from app.browser import capture_screenshots
from app.diff import compare_images
from app.compressor import compress_and_resize
from app.evaluator import evaluate_layout

COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_CYAN = "\033[36m"

# Avoid crashes on Windows encoding issues (e.g. CP950)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(errors='replace')
    except Exception:
        pass

def load_config():
    """Loads visual_qa_config.json if available, else returns default settings."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(script_dir, "visual_qa_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Default settings
    return {
        "viewports": {
            "mobile": {"width": 375, "height": 812},
            "tablet": {"width": 768, "height": 1024},
            "desktop": {"width": 1920, "height": 1080}
        },
        "diff_threshold_percent": 0.1,
        "pixel_diff_tolerance": 15,
        "compress_max_width": 1024,
        "compress_quality": 80,
        "output_dir": ".visual_qa"
    }

def print_banner():
    print(f"\n{COLOR_CYAN}{COLOR_BOLD}[VISUAL-QA] AI Visual Auto-Layout Checker{COLOR_RESET}")
    print("==================================================")

def cmd_check(args, config):
    url_or_path = args.url_or_path
    output_dir = config.get("output_dir", ".visual_qa")
    
    baseline_dir = os.path.join(output_dir, "baseline")
    current_dir = os.path.join(output_dir, "current")
    diff_dir = os.path.join(output_dir, "diff")
    
    viewports = config.get("viewports")
    
    # 1. Check if baselines already exist
    has_baseline = True
    for vp in viewports:
        baseline_file = os.path.join(baseline_dir, f"screenshot_{vp}.png")
        if not os.path.exists(baseline_file):
            has_baseline = False
            break
            
    # Force baseline generation if requested or missing
    if args.baseline or not has_baseline:
        print(f"{COLOR_YELLOW}[VISUAL-QA] Baseline screenshots not found or --baseline forced. Generating baselines...{COLOR_RESET}")
        capture_screenshots(url_or_path, baseline_dir, viewports=viewports, wait_ms=args.wait)
        print(f"{COLOR_GREEN}[VISUAL-QA] Baseline screenshots successfully generated under {baseline_dir}!{COLOR_RESET}")
        return 0
        
    # 2. Capture current screen
    print(f"{COLOR_BLUE}[VISUAL-QA] Capturing current screenshots for comparison...{COLOR_RESET}")
    current_screenshots = capture_screenshots(url_or_path, current_dir, viewports=viewports, wait_ms=args.wait)
    
    # 3. Perform local pixel-by-pixel comparisons
    diff_detected = False
    diff_reports = {}
    
    for vp in viewports:
        baseline_path = os.path.join(baseline_dir, f"screenshot_{vp}.png")
        current_path = current_screenshots[vp]
        diff_path = os.path.join(diff_dir, f"diff_{vp}.png")
        
        threshold = config.get("diff_threshold_percent", 0.1)
        tolerance = config.get("pixel_diff_tolerance", 15)
        
        diff_pct, similar = compare_images(
            baseline_path, 
            current_path, 
            diff_output_path=diff_path, 
            threshold_percent=threshold,
            tolerance=tolerance
        )
        
        if not similar:
            diff_detected = True
            diff_reports[vp] = {
                "diff_percent": diff_pct,
                "current_path": current_path,
                "diff_path": diff_path
            }
            print(f"  - Viewport {COLOR_YELLOW}{vp}{COLOR_RESET}: {COLOR_RED}MISMATCH{COLOR_RESET} ({diff_pct:.3f}% pixels changed)")
        else:
            print(f"  - Viewport {COLOR_YELLOW}{vp}{COLOR_RESET}: {COLOR_GREEN}PASS{COLOR_RESET} ({diff_pct:.3f}% difference)")
            
    if not diff_detected:
        print(f"\n{COLOR_GREEN}[VISUAL-QA] SUCCESS: No significant visual changes detected. Baseline matches!{COLOR_RESET}")
        return 0
        
    print(f"\n{COLOR_RED}[VISUAL-QA] ALERT: Visual differences detected! Triggering Gemini Vision layout audit...{COLOR_RESET}")
    
    # 4. Trigger Gemini evaluation for mismatched viewports
    any_issues = False
    for vp, info in diff_reports.items():
        print(f"\n--- Auditing {COLOR_YELLOW}{vp}{COLOR_RESET} viewport ({info['diff_percent']:.2f}% diff) ---")
        
        # Compress current screenshot to save tokens
        compressed_path = os.path.join(output_dir, f"screenshot_{vp}_compressed.webp")
        compress_and_resize(
            info["current_path"],
            output_path=compressed_path,
            max_width=config.get("compress_max_width", 1024),
            quality=config.get("compress_quality", 80),
            format="WEBP"
        )
        
        try:
            print(f"{COLOR_BLUE}[VISUAL-QA] Requesting Gemini Vision assessment for {vp}...{COLOR_RESET}")
            report = evaluate_layout(compressed_path, config=config)
            
            if report.get("has_issues", False):
                any_issues = True
                print(f"{COLOR_RED}[!] Visual Layout Issues Found in {vp} view:{COLOR_RESET}")
                for i, issue in enumerate(report.get("issues", [])):
                    severity_color = COLOR_RED if issue.get("severity") == "critical" else COLOR_YELLOW
                    print(f"  {COLOR_BOLD}{i+1}. [{issue.get('type').upper()}] ({issue.get('severity').upper()}){COLOR_RESET}")
                    print(f"     Description: {issue.get('description')}")
                    print(f"     Location:    {issue.get('selector_or_location')}")
                    print(f"     Suggested CSS Fix:\n     {COLOR_GREEN}{issue.get('suggested_fix')}{COLOR_RESET}")
            else:
                print(f"{COLOR_GREEN}[VISUAL-QA] Gemini checked the changes and found no semantic layout issues. Safe to proceed!{COLOR_RESET}")
                
        except Exception as e:
            print(f"{COLOR_RED}[VISUAL-QA] Error during Gemini evaluation: {e}{COLOR_RESET}")
            return 2
            
    if any_issues:
        print(f"\n{COLOR_RED}[VISUAL-QA] FAILED: Layout issues detected. Review diff highlights in {diff_dir}{COLOR_RESET}")
        return 1
    else:
        print(f"\n{COLOR_GREEN}[VISUAL-QA] SUCCESS: Differences exist but no layout defects were detected by Gemini.{COLOR_RESET}")
        return 0

def cmd_approve(args, config):
    output_dir = config.get("output_dir", ".visual_qa")
    baseline_dir = os.path.join(output_dir, "baseline")
    current_dir = os.path.join(output_dir, "current")
    
    if not os.path.exists(current_dir):
        print(f"{COLOR_RED}[VISUAL-QA] No current screenshots exist to approve.{COLOR_RESET}")
        return 1
        
    os.makedirs(baseline_dir, exist_ok=True)
    
    approved_count = 0
    for filename in os.listdir(current_dir):
        if filename.startswith("screenshot_") and filename.endswith(".png"):
            src = os.path.join(current_dir, filename)
            dest = os.path.join(baseline_dir, filename)
            shutil.copy(src, dest)
            approved_count += 1
            
    print(f"{COLOR_GREEN}[VISUAL-QA] Successfully approved {approved_count} baseline screenshots!{COLOR_RESET}")
    return 0

def cmd_status(args, config):
    output_dir = config.get("output_dir", ".visual_qa")
    baseline_dir = os.path.join(output_dir, "baseline")
    
    print_banner()
    print(f"Baseline directory: {os.path.abspath(baseline_dir)}")
    
    if os.path.exists(baseline_dir):
        baselines = [f for f in os.listdir(baseline_dir) if f.startswith("screenshot_") and f.endswith(".png")]
        print(f"Total Baselines:    {len(baselines)}")
        for b in baselines:
            print(f"  - {b}")
    else:
        print("Total Baselines:    0 (Run 'visual-qa check <url> --baseline' to create them)")
        
    print(f"Default Viewports:  {list(config.get('viewports', {}).keys())}")
    print(f"Diff Threshold:     {config.get('diff_threshold_percent')}%")
    print(f"Pixel Tolerance:    {config.get('pixel_diff_tolerance')}")
    print("==================================================")
    return 0

def main():
    config = load_config()
    
    parser = argparse.ArgumentParser(description="Agent-Visual-QA CLI tool.")
    subparsers = parser.add_subparsers(dest="command")
    
    # Check command
    parser_check = subparsers.add_parser("check", help="Capture and compare visual state.")
    parser_check.add_argument("url_or_path", help="Web URL or local HTML file path.")
    parser_check.add_argument("--baseline", action="store_true", help="Force baseline generation.")
    parser_check.add_argument("--wait", type=int, default=1000, help="Wait timeout after navigation in ms.")
    
    # Approve command
    subparsers.add_parser("approve", help="Promote current screenshots to baseline.")
    
    # Status command
    subparsers.add_parser("status", help="Show configurations and baseline counts.")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    if args.command == "check":
        sys.exit(cmd_check(args, config))
    elif args.command == "approve":
        sys.exit(cmd_approve(args, config))
    elif args.command == "status":
        sys.exit(cmd_status(args, config))

if __name__ == "__main__":
    main()
