#!/usr/bin/env python3
"""
E2E Test Results Analyzer

Analyzes the JSON results from E2E integration tests and generates:
- Human-readable summary report
- Performance analysis
- Failure investigation
- Recommendations

Usage:
    python scripts/analyze_e2e_results.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class E2EResultsAnalyzer:
    """Analyzes E2E test results and generates reports"""

    def __init__(self, results_file: str = "logs/e2e_integration_results.json"):
        self.results_file = Path(results_file)
        self.results = self._load_results()

    def _load_results(self) -> Dict:
        """Load results from JSON file"""
        if not self.results_file.exists():
            print(f"❌ Results file not found: {self.results_file}")
            sys.exit(1)

        with open(self.results_file, 'r') as f:
            return json.load(f)

    def generate_summary_report(self) -> str:
        """Generate summary report"""
        lines = []
        lines.append("=" * 80)
        lines.append("KeneyApp E2E Integration Test Analysis Report")
        lines.append("=" * 80)
        lines.append("")

        # Test Run Info
        lines.append("📋 Test Run Information")
        lines.append(f"  Run ID:       {self.results['test_run_id']}")
        lines.append(f"  Start Time:   {self.results['start_time']}")
        lines.append(f"  End Time:     {self.results['end_time']}")
        lines.append(f"  Duration:     {self.results['total_duration_seconds']:.2f}s")
        lines.append("")

        # Summary
        summary = self.results['summary']
        lines.append("📊 Test Summary")
        lines.append(f"  Total Tests:  {summary['total']}")
        lines.append(f"  ✅ Passed:     {summary['passed']}")
        lines.append(f"  ❌ Failed:     {summary['failed']}")
        lines.append(f"  ⏭️  Skipped:    {summary['skipped']}")

        pass_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0
        lines.append(f"  Pass Rate:    {pass_rate:.1f}%")
        lines.append("")

        return "\n".join(lines)

    def analyze_performance(self) -> str:
        """Analyze performance metrics"""
        lines = []
        lines.append("⚡ Performance Analysis")
        lines.append("-" * 80)

        metrics = self.results.get('performance_metrics', {})
        if not metrics:
            lines.append("  No performance metrics available")
            return "\n".join(lines)

        # Group metrics by category
        auth_metrics = {k: v for k, v in metrics.items() if 'auth' in k}
        patient_metrics = {k: v for k, v in metrics.items() if 'patient' in k}
        other_metrics = {k: v for k, v in metrics.items()
                        if k not in auth_metrics and k not in patient_metrics}

        if auth_metrics:
            lines.append("\n  Authentication Performance:")
            for name, data in auth_metrics.items():
                lines.append(f"    {name}: {data['value']:.2f} {data['unit']}")

        if patient_metrics:
            lines.append("\n  Patient Operations Performance:")
            for name, data in patient_metrics.items():
                lines.append(f"    {name}: {data['value']:.2f} {data['unit']}")

        if other_metrics:
            lines.append("\n  Other Metrics:")
            for name, data in other_metrics.items():
                lines.append(f"    {name}: {data['value']:.2f} {data['unit']}")

        # Performance Assessment
        lines.append("\n  Performance Assessment:")

        # Check response times
        slow_operations = []
        for name, data in metrics.items():
            if data['unit'] == 'ms' and data['value'] > 500:
                slow_operations.append((name, data['value']))

        if slow_operations:
            lines.append("    ⚠️  Slow Operations Detected:")
            for op, time in slow_operations:
                lines.append(f"      - {op}: {time:.2f}ms (>500ms)")
        else:
            lines.append("    ✅ All operations within acceptable response times")

        lines.append("")
        return "\n".join(lines)

    def analyze_failures(self) -> str:
        """Analyze test failures"""
        lines = []
        lines.append("🔍 Failure Analysis")
        lines.append("-" * 80)

        errors = self.results.get('errors', [])
        if not errors:
            lines.append("  ✅ No failures detected")
            lines.append("")
            return "\n".join(lines)

        lines.append(f"  Total Errors: {len(errors)}")
        lines.append("")

        for i, error in enumerate(errors, 1):
            lines.append(f"  Error #{i}:")
            lines.append(f"    Test:      {error['test']}")
            lines.append(f"    Error:     {error['error']}")
            lines.append(f"    Timestamp: {error['timestamp']}")
            if error.get('traceback'):
                lines.append(f"    Traceback:")
                for line in error['traceback'].split('\n'):
                    lines.append(f"      {line}")
            lines.append("")

        return "\n".join(lines)

    def get_test_details(self) -> str:
        """Get detailed test results"""
        lines = []
        lines.append("📝 Detailed Test Results")
        lines.append("-" * 80)

        tests = self.results.get('tests', [])

        # Group by status
        passed = [t for t in tests if t['status'] == 'passed']
        failed = [t for t in tests if t['status'] == 'failed']
        skipped = [t for t in tests if t['status'] == 'skipped']

        if passed:
            lines.append(f"\n  ✅ Passed Tests ({len(passed)}):")
            for test in passed:
                lines.append(f"    • {test['name']} ({test['duration_seconds']:.2f}s)")

        if failed:
            lines.append(f"\n  ❌ Failed Tests ({len(failed)}):")
            for test in failed:
                lines.append(f"    • {test['name']} ({test['duration_seconds']:.2f}s)")
                if test.get('details'):
                    lines.append(f"      Details: {json.dumps(test['details'], indent=6)}")

        if skipped:
            lines.append(f"\n  ⏭️  Skipped Tests ({len(skipped)}):")
            for test in skipped:
                lines.append(f"    • {test['name']}")

        lines.append("")
        return "\n".join(lines)

    def generate_recommendations(self) -> str:
        """Generate recommendations based on results"""
        lines = []
        lines.append("💡 Recommendations")
        lines.append("-" * 80)

        recommendations = []

        # Check pass rate
        summary = self.results['summary']
        pass_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0

        if pass_rate < 100:
            recommendations.append(
                f"⚠️  Pass rate is {pass_rate:.1f}%. Investigate and fix failing tests."
            )
        else:
            recommendations.append("✅ All tests passing. Excellent!")

        # Check performance
        metrics = self.results.get('performance_metrics', {})
        slow_ops = [k for k, v in metrics.items()
                   if v.get('unit') == 'ms' and v.get('value', 0) > 500]

        if slow_ops:
            recommendations.append(
                f"⚡ {len(slow_ops)} operation(s) are slow (>500ms). Consider optimization."
            )

        # Check errors
        errors = self.results.get('errors', [])
        if errors:
            error_types = {}
            for error in errors:
                error_msg = error['error']
                error_types[error_msg] = error_types.get(error_msg, 0) + 1

            recommendations.append(
                f"🔍 {len(errors)} error(s) detected. Top issues:"
            )
            for msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                recommendations.append(f"   - {msg} (occurred {count}x)")

        # Check duration
        duration = self.results.get('total_duration_seconds', 0)
        if duration > 120:
            recommendations.append(
                f"⏱️  Test suite took {duration:.1f}s. Consider parallelization for faster execution."
            )
        elif duration < 30:
            recommendations.append(
                "✅ Test suite execution time is excellent!"
            )

        if not recommendations:
            recommendations.append("✅ No issues detected. System is performing well!")

        for rec in recommendations:
            lines.append(f"  {rec}")

        lines.append("")
        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """Generate complete analysis report"""
        sections = [
            self.generate_summary_report(),
            self.analyze_performance(),
            self.get_test_details(),
            self.analyze_failures(),
            self.generate_recommendations(),
        ]

        report = "\n".join(sections)
        report += "=" * 80 + "\n"

        return report

    def save_report(self, output_file: str = "logs/e2e_analysis_report.txt"):
        """Save report to file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_full_report()

        with open(output_path, 'w') as f:
            f.write(report)

        print(f"📄 Report saved to: {output_path}")
        return output_path

    def print_report(self):
        """Print report to console"""
        print(self.generate_full_report())


def main():
    """Main entry point"""
    print("🔍 Analyzing E2E Test Results...\n")

    analyzer = E2EResultsAnalyzer()

    # Print to console
    analyzer.print_report()

    # Save to file
    report_path = analyzer.save_report()

    # Determine exit code based on test results
    summary = analyzer.results['summary']
    if summary['failed'] > 0:
        print(f"\n❌ Tests failed. See {report_path} for details.")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed! Report: {report_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
