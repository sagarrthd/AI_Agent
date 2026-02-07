"""
WIF ECM Test Case Validators
Zero-tolerance validation for ASIL-A compliance
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from .models import (
    WIFTestCase,
    WIFRequirement,
    ValidationError,
    CoverageReport,
    RequirementType,
    ASILLevel
)


class TestCaseValidator:
    """
    Production-grade validator for WIF ECM test cases
    Implements zero-tolerance validation rules
    """
    
    # Regex patterns for ID validation
    SYSTEM_TC_PATTERN = re.compile(r'^TC_SYS_SYS_WIF_\d{3}_\d{3}$')
    SOFTWARE_TC_PATTERN = re.compile(r'^TC_SW_SW_WIF_\d{3}_\d{3}$')
    DIAGNOSTIC_TC_PATTERN = re.compile(r'^TC_DIAG_DIAG_WIF_\d{3}_\d{3}$')
    
    # DTC code pattern (P + 4 hex digits)
    DTC_PATTERN = re.compile(r'^P[0-9A-Fa-f]{4}$')
    
    # A2L parameter pattern
    A2L_PATTERN = re.compile(r'^CAL_WIF_\w+$')
    
    # Requirement ID patterns
    SYS_REQ_PATTERN = re.compile(r'^SYS_WIF_\d{3}$')
    SW_REQ_PATTERN = re.compile(r'^SW_WIF_\d{3}$')
    DIAG_REQ_PATTERN = re.compile(r'^DIAG_WIF_\d{3}$')
    
    def __init__(self, 
                 requirements: Dict[str, WIFRequirement],
                 a2l_parameters: Optional[Set[str]] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize validator with requirements and A2L parameters
        
        Args:
            requirements: Dictionary of requirement ID -> WIFRequirement
            a2l_parameters: Set of valid A2L parameter names
            logger: Optional logger for error reporting
        """
        self.requirements = requirements
        self.a2l_parameters = a2l_parameters or set()
        self.logger = logger or logging.getLogger(__name__)
        self.errors: List[ValidationError] = []
        
    def validate_test_case(self, tc: WIFTestCase) -> Tuple[bool, List[ValidationError]]:
        """
        Validate a single test case against all rules
        
        Args:
            tc: Test case to validate
            
        Returns:
            Tuple of (is_valid, list of errors) - only CRITICAL errors cause is_valid=False
        """
        errors = []
        
        # 1. Requirement ID must exist in source
        if tc.requirement_id not in self.requirements:
            errors.append(ValidationError(
                test_case_id=tc.test_case_id,
                error_type="INVALID_REQUIREMENT_REF",
                message=f"Requirement '{tc.requirement_id}' not found in requirements"
            ))
        else:
            req = self.requirements[tc.requirement_id]
            
            # 2. ASIL level must match requirement
            if tc.asil_level != req.asil_level:
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="ASIL_MISMATCH",
                    message=f"Req ASIL={req.asil_level.value}, TC ASIL={tc.asil_level.value}"
                ))
            
            # 3. Type must match requirement
            if tc.type != req.req_type:
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="TYPE_MISMATCH",
                    message=f"Req Type={req.req_type.value}, TC Type={tc.type.value}"
                ))
        
        # 4. Test case ID format check based on type
        id_valid = self._validate_test_case_id(tc)
        if not id_valid:
            errors.append(ValidationError(
                test_case_id=tc.test_case_id,
                error_type="INVALID_ID_FORMAT",
                message=f"ID '{tc.test_case_id}' does not match expected format for {tc.type.value} tests"
            ))
        
        # 5. DTC codes must be valid for diagnostic tests
        if tc.type == RequirementType.DIAGNOSTIC or "DIAG" in tc.requirement_id:
            if tc.dtc_code and not self.DTC_PATTERN.match(tc.dtc_code):
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="INVALID_DTC_CODE",
                    message=f"DTC code '{tc.dtc_code}' does not match format P[0-9A-F]{{4}}"
                ))
        
        # 6. A2L reference must exist in calibration set
        if tc.traceability.a2l_reference:
            if not self.A2L_PATTERN.match(tc.traceability.a2l_reference):
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="INVALID_A2L_FORMAT",
                    message=f"A2L reference '{tc.traceability.a2l_reference}' does not match CAL_WIF_* format"
                ))
            elif self.a2l_parameters and tc.traceability.a2l_reference not in self.a2l_parameters:
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="INVALID_A2L_REF",
                    message=f"A2L reference '{tc.traceability.a2l_reference}' not found in calibration parameters"
                ))
        
        # 7. Test steps must be atomic and measurable
        step_errors = self._validate_test_steps(tc)
        errors.extend(step_errors)
        
        # 8. Traceability must be complete
        trace_errors = self._validate_traceability(tc)
        errors.extend(trace_errors)
        
        # 9. Pass criteria must be unambiguous
        if not tc.pass_criteria or len(tc.pass_criteria) < 10:
            errors.append(ValidationError(
                test_case_id=tc.test_case_id,
                error_type="VAGUE_PASS_CRITERIA",
                message="Pass criteria must be specific and unambiguous (min 10 chars)"
            ))
        
        # Log errors (warnings as warnings, critical as errors)
        for error in errors:
            if error.severity == "WARNING":
                self.logger.warning(str(error))
            else:
                self.logger.error(str(error))
            self.errors.append(error)
        
        # Only CRITICAL errors cause validation failure
        critical_errors = [e for e in errors if e.severity == "CRITICAL"]
        return len(critical_errors) == 0, errors
    
    def _validate_test_case_id(self, tc: WIFTestCase) -> bool:
        """Validate test case ID format based on type"""
        if tc.type == RequirementType.SYSTEM:
            return bool(self.SYSTEM_TC_PATTERN.match(tc.test_case_id))
        elif tc.type == RequirementType.SOFTWARE:
            return bool(self.SOFTWARE_TC_PATTERN.match(tc.test_case_id))
        elif tc.type == RequirementType.DIAGNOSTIC:
            return bool(self.DIAGNOSTIC_TC_PATTERN.match(tc.test_case_id))
        return False
    
    def _validate_test_steps(self, tc: WIFTestCase) -> List[ValidationError]:
        """Validate test steps are atomic and measurable"""
        errors = []
        
        if not tc.test_steps:
            errors.append(ValidationError(
                test_case_id=tc.test_case_id,
                error_type="NO_TEST_STEPS",
                message="Test case must have at least one test step"
            ))
            return errors
        
        vague_patterns = [
            r'^\s*check\s*$',
            r'^\s*verify\s*$',
            r'^\s*test\s*$',
            r'^\s*confirm\s*$',
            r'if\s+working',
            r'working\s+correctly',
            r'as\s+expected',
        ]
        
        for step in tc.test_steps:
            # Check for vague actions
            for pattern in vague_patterns:
                if re.search(pattern, step.action, re.IGNORECASE):
                    errors.append(ValidationError(
                        test_case_id=tc.test_case_id,
                        error_type="VAGUE_ACTION",
                        message=f"Step {step.step_no}: Action is too vague: '{step.action}'"
                    ))
                    break
            
            # Check for vague expected results
            for pattern in vague_patterns:
                if re.search(pattern, step.expected_result, re.IGNORECASE):
                    errors.append(ValidationError(
                        test_case_id=tc.test_case_id,
                        error_type="VAGUE_EXPECTED_RESULT",
                        message=f"Step {step.step_no}: Expected result is too vague: '{step.expected_result}'"
                    ))
                    break
            
            # Check step has measurable content (contains numbers, operators, or specific values)
            measurable_pattern = r'[<>=≤≥]|\d+|true|false|0x[0-9A-Fa-f]+'
            if not re.search(measurable_pattern, step.expected_result, re.IGNORECASE):
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="NON_MEASURABLE_RESULT",
                    message=f"Step {step.step_no}: Expected result should be quantifiable",
                    severity="WARNING"
                ))
        
        return errors
    
    def _validate_traceability(self, tc: WIFTestCase) -> List[ValidationError]:
        """Validate traceability block completeness"""
        errors = []
        trace = tc.traceability
        
        # System tests must have system_req
        if tc.type == RequirementType.SYSTEM and not trace.system_req:
            errors.append(ValidationError(
                test_case_id=tc.test_case_id,
                error_type="MISSING_SYSTEM_TRACE",
                message="System test must have system_req in traceability"
            ))
        
        # Software tests should trace to system req if parent exists
        if tc.type == RequirementType.SOFTWARE:
            if not trace.software_req:
                errors.append(ValidationError(
                    test_case_id=tc.test_case_id,
                    error_type="MISSING_SOFTWARE_TRACE",
                    message="Software test must have software_req in traceability"
                ))
            
            # Check parent reference
            if tc.requirement_id in self.requirements:
                req = self.requirements[tc.requirement_id]
                if req.parent_system_req and not trace.system_req:
                    errors.append(ValidationError(
                        test_case_id=tc.test_case_id,
                        error_type="MISSING_PARENT_TRACE",
                        message=f"Requirement has parent '{req.parent_system_req}' but not traced"
                    ))
        
        # Diagnostic tests must have diagnostic_req
        if tc.type == RequirementType.DIAGNOSTIC and not trace.diagnostic_req:
            errors.append(ValidationError(
                test_case_id=tc.test_case_id,
                error_type="MISSING_DIAGNOSTIC_TRACE",
                message="Diagnostic test must have diagnostic_req in traceability"
            ))
        
        return errors
    
    def validate_all(self, test_cases: List[WIFTestCase]) -> Tuple[bool, List[ValidationError]]:
        """
        Validate all test cases
        
        Args:
            test_cases: List of test cases to validate
            
        Returns:
            Tuple of (all_valid, list of all errors) - all_valid is True if no CRITICAL errors
        """
        all_errors = []
        all_valid = True
        
        for tc in test_cases:
            is_valid, errors = self.validate_test_case(tc)
            if not is_valid:
                all_valid = False
            all_errors.extend(errors)
        
        # Summary log
        critical_count = sum(1 for e in all_errors if e.severity == "CRITICAL")
        warning_count = sum(1 for e in all_errors if e.severity == "WARNING")
        
        if critical_count > 0:
            self.logger.error(f"Validation: {critical_count} CRITICAL errors, {warning_count} warnings")
        elif warning_count > 0:
            self.logger.info(f"Validation: {warning_count} warnings (non-blocking)")
        
        return all_valid, all_errors
    
    def get_critical_error_count(self) -> int:
        """Get count of critical errors only"""
        return sum(1 for e in self.errors if e.severity == "CRITICAL")
    
    def validate_coverage(self, test_cases: List[WIFTestCase]) -> CoverageReport:
        """
        Validate 100% requirement coverage
        
        Args:
            test_cases: List of all generated test cases
            
        Returns:
            CoverageReport with coverage analysis
        """
        report = CoverageReport()
        
        # Count requirements by type
        sys_reqs = set()
        sw_reqs = set()
        diag_reqs = set()
        
        for req_id, req in self.requirements.items():
            if req.req_type == RequirementType.SYSTEM:
                sys_reqs.add(req_id)
            elif req.req_type == RequirementType.SOFTWARE:
                sw_reqs.add(req_id)
            elif req.req_type == RequirementType.DIAGNOSTIC:
                diag_reqs.add(req_id)
        
        report.total_requirements = len(self.requirements)
        
        # Count test cases and track coverage
        covered_reqs = set()
        
        for tc in test_cases:
            covered_reqs.add(tc.requirement_id)
            
            if tc.type == RequirementType.SYSTEM:
                report.system_test_cases += 1
            elif tc.type == RequirementType.SOFTWARE:
                report.software_test_cases += 1
            elif tc.type == RequirementType.DIAGNOSTIC:
                report.diagnostic_test_cases += 1
        
        report.total_test_cases = len(test_cases)
        report.covered_requirements = len(covered_reqs)
        
        # Find uncovered requirements
        all_req_ids = set(self.requirements.keys())
        uncovered = all_req_ids - covered_reqs
        report.uncovered_requirements = list(sorted(uncovered))
        
        # Calculate coverage
        if report.total_requirements > 0:
            report.coverage_percentage = (report.covered_requirements / report.total_requirements) * 100.0
        else:
            report.coverage_percentage = 100.0
        
        # Log uncovered requirements
        for req_id in report.uncovered_requirements:
            self.logger.error(f"CRITICAL: Requirement '{req_id}' has ZERO test cases!")
            self.errors.append(ValidationError(
                test_case_id="N/A",
                error_type="UNCOVERED_REQUIREMENT",
                message=f"Requirement '{req_id}' has no test cases"
            ))
        
        return report
    
    def get_all_errors(self) -> List[ValidationError]:
        """Get all accumulated validation errors"""
        return self.errors
    
    def clear_errors(self):
        """Clear accumulated errors"""
        self.errors = []
