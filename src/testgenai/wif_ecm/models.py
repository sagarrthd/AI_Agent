"""
WIF ECM Data Models
Strict dataclasses for ASIL-A compliant test case generation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class RequirementType(Enum):
    """Type of requirement for proper categorization"""
    SYSTEM = "System"
    SOFTWARE = "Software"
    DIAGNOSTIC = "Diagnostic"


class ASILLevel(Enum):
    """ASIL safety levels per ISO 26262"""
    ASIL_A = "ASIL-A"
    ASIL_B = "ASIL-B"
    ASIL_C = "ASIL-C"
    ASIL_D = "ASIL-D"
    QM = "QM"


class VerificationMethod(Enum):
    """Verification method for test steps"""
    AUTOMATED = "Automated"
    MANUAL = "Manual"


class TestEnvironment(Enum):
    """Test environment types"""
    HIL = "HIL"
    SIL = "SIL"
    MIL = "MIL"
    VEHICLE = "Vehicle"


@dataclass
class Traceability:
    """Traceability block for parent-child requirement mapping"""
    system_req: Optional[str] = None
    software_req: Optional[str] = None
    diagnostic_req: Optional[str] = None
    a2l_reference: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "system_req": self.system_req,
            "software_req": self.software_req,
            "diagnostic_req": self.diagnostic_req,
            "a2l_reference": self.a2l_reference
        }


@dataclass
class WIFRequirement:
    """
    Requirement model for WIF ECM
    Stores all metadata needed for test case generation
    """
    req_id: str
    description: str
    req_type: RequirementType
    asil_level: ASILLevel = ASILLevel.QM
    parent_system_req: Optional[str] = None
    dtc_code: Optional[str] = None
    calibration_params: List[str] = field(default_factory=list)
    
    # Raw text for verbatim copying
    raw_text: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "req_id": self.req_id,
            "description": self.description,
            "req_type": self.req_type.value,
            "asil_level": self.asil_level.value,
            "parent_system_req": self.parent_system_req,
            "dtc_code": self.dtc_code,
            "calibration_params": self.calibration_params,
        }


@dataclass
class WIFTestStep:
    """
    Single atomic test step
    Must be measurable and verifiable
    """
    step_no: int
    action: str
    expected_result: str
    verification_method: VerificationMethod = VerificationMethod.AUTOMATED
    
    def to_dict(self) -> Dict:
        return {
            "step_no": self.step_no,
            "action": self.action,
            "expected_result": self.expected_result,
            "verification_method": self.verification_method.value
        }


@dataclass
class WIFTestCase:
    """
    Complete test case for WIF ECM validation
    Follows strict JSON structure for traceability
    """
    test_case_id: str
    type: RequirementType
    requirement_id: str
    requirement_description: str
    test_objective: str
    preconditions: List[str] = field(default_factory=list)
    test_steps: List[WIFTestStep] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    pass_criteria: str = ""
    traceability: Traceability = field(default_factory=Traceability)
    test_environment: TestEnvironment = TestEnvironment.HIL
    test_tools: List[str] = field(default_factory=list)
    asil_level: ASILLevel = ASILLevel.QM
    dtc_code: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "test_case_id": self.test_case_id,
            "type": self.type.value,
            "requirement_id": self.requirement_id,
            "requirement_description": self.requirement_description,
            "test_objective": self.test_objective,
            "preconditions": self.preconditions,
            "test_steps": [step.to_dict() for step in self.test_steps],
            "postconditions": self.postconditions,
            "pass_criteria": self.pass_criteria,
            "traceability": self.traceability.to_dict(),
            "test_environment": self.test_environment.value,
            "test_tools": self.test_tools,
            "asil_level": self.asil_level.value,
            "dtc_code": self.dtc_code
        }


@dataclass
class ValidationError:
    """Validation error with severity and details"""
    test_case_id: str
    error_type: str
    message: str
    severity: str = "CRITICAL"
    
    def __str__(self) -> str:
        return f"[{self.severity}] {self.test_case_id}: {self.error_type} - {self.message}"


@dataclass
class CoverageReport:
    """Coverage analysis report"""
    total_requirements: int = 0
    covered_requirements: int = 0
    total_test_cases: int = 0
    system_test_cases: int = 0
    software_test_cases: int = 0
    diagnostic_test_cases: int = 0
    uncovered_requirements: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0
    
    def is_complete(self) -> bool:
        """Check if 100% coverage is achieved"""
        return self.coverage_percentage >= 100.0 and len(self.uncovered_requirements) == 0
