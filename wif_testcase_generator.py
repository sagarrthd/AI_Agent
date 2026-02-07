#!/usr/bin/env python3
"""
WIF ECM Test Case Generator - Standalone Runner
Production-grade test case generation for automotive ECM validation
ASIL-A Safety Critical Software

Usage:
    python wif_testcase_generator.py <requirements_file> [--output <output_dir>]
    
Example:
    python wif_testcase_generator.py WIF_ECM_Requirements_Specification.xlsx --output ./test_output
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from testgenai.wif_ecm import WIFTestCaseGenerator


def print_banner():
    """Print startup banner"""
    print("=" * 70)
    print("  WIF ECM TEST CASE GENERATOR")
    print("  ASIL-A Safety Critical Software")
    print("  ISO 26262 Compliant Test Case Generation")
    print("=" * 70)
    print()


def main():
    """Main entry point"""
    import argparse
    
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="WIF ECM Test Case Generator - ASIL-A Compliant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Files:
  WIF_System_TestCases.json         - System requirement test cases
  WIF_Software_TestCases.json       - Software requirement test cases  
  WIF_Diagnostic_TestCases.json     - Diagnostic requirement test cases
  WIF_TestCases_Traceability_Matrix.xlsx - Full traceability matrix
  test_generation_errors.log        - Error log file

Example:
  python wif_testcase_generator.py requirements.xlsx --output ./output
        """
    )
    
    parser.add_argument(
        "requirements_file",
        help="Path to requirements Excel file (e.g., WIF_ECM_Requirements_Specification.xlsx)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory for generated files (default: output)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.requirements_file):
        print(f"ERROR: Requirements file not found: {args.requirements_file}")
        print("\nExpected file format: Excel (.xlsx) with sheets:")
        print("  - 'System Requirements'")
        print("  - 'Software Requirements'")
        print("  - 'Diagnostic Requirements'")
        print("  - 'Calibration Parameters' (optional)")
        return 1
    
    print(f"Input:  {args.requirements_file}")
    print(f"Output: {args.output}")
    print()
    
    # Run generator
    try:
        generator = WIFTestCaseGenerator(args.requirements_file, args.output)
        success = generator.run()
        
        if success:
            print()
            print("=" * 70)
            print("  ✓ GENERATION COMPLETE - 100% COVERAGE ACHIEVED")
            print("=" * 70)
            print()
            print("Generated files:")
            print(f"  - {args.output}/WIF_System_TestCases.json")
            print(f"  - {args.output}/WIF_Software_TestCases.json")
            print(f"  - {args.output}/WIF_Diagnostic_TestCases.json")
            print(f"  - {args.output}/WIF_TestCases_Traceability_Matrix.xlsx")
            return 0
        else:
            print()
            print("=" * 70)
            print("  ✗ GENERATION FAILED - CHECK ERROR LOG")
            print("=" * 70)
            print()
            print(f"See error log: {args.output}/test_generation_errors.log")
            return 1
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
