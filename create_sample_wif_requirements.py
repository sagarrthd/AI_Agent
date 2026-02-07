#!/usr/bin/env python3
"""
Create sample WIF ECM Requirements Excel file for testing
"""

import pandas as pd
from pathlib import Path


def create_sample_requirements():
    """Create sample WIF ECM requirements Excel file"""
    
    output_path = Path("sample_inputs/WIF_ECM_Requirements_Specification.xlsx")
    output_path.parent.mkdir(exist_ok=True)
    
    # System Requirements
    system_reqs = pd.DataFrame({
        "Req_ID": [
            "SYS_WIF_001",
            "SYS_WIF_002",
            "SYS_WIF_003",
            "SYS_WIF_004",
            "SYS_WIF_005",
        ],
        "Description": [
            "The ECM shall detect water in fuel when sensor resistance is below 1000 ohms",
            "The ECM shall activate water warning indicator within 200ms of water detection",
            "The ECM shall store DTC P242F when water is detected in fuel filter",
            "The ECM shall inhibit fuel injection if water level exceeds critical threshold",
            "The ECM shall reset water detection status when sensor resistance exceeds 5000 ohms",
        ],
        "ASIL_Level": [
            "ASIL-A",
            "ASIL-A",
            "ASIL-A",
            "ASIL-A",
            "QM",
        ],
        "Calibration_Params": [
            "CAL_WIF_Resistance_Threshold",
            "CAL_WIF_Warning_Delay",
            "CAL_WIF_DTC_Debounce",
            "CAL_WIF_Critical_Level",
            "CAL_WIF_Reset_Threshold",
        ],
    })
    
    # Software Requirements
    software_reqs = pd.DataFrame({
        "Req_ID": [
            "SW_WIF_001",
            "SW_WIF_002",
            "SW_WIF_003",
            "SW_WIF_004",
            "SW_WIF_005",
            "SW_WIF_006",
        ],
        "Description": [
            "The WIF sensor reading function shall sample ADC at 10ms intervals",
            "The WIF status calculation shall apply debounce of 5 consecutive samples",
            "The WIF module shall calculate sensor resistance from ADC counts using calibration curve",
            "The WIF module shall update CAN signal WIF_Status every 100ms",
            "The WIF fault detection shall trigger callback to DTC handler when threshold exceeded",
            "The WIF module shall validate sensor input range 0-65535 ADC counts",
        ],
        "ASIL_Level": [
            "ASIL-A",
            "ASIL-A",
            "ASIL-A",
            "ASIL-A",
            "ASIL-A",
            "QM",
        ],
        "Parent_System_Req": [
            "SYS_WIF_001",
            "SYS_WIF_002",
            "SYS_WIF_001",
            "SYS_WIF_002",
            "SYS_WIF_003",
            "SYS_WIF_001",
        ],
        "Calibration_Params": [
            "CAL_WIF_Sample_Rate",
            "CAL_WIF_Debounce_Count",
            "CAL_WIF_Cal_Curve_A, CAL_WIF_Cal_Curve_B",
            "CAL_WIF_CAN_Period",
            "CAL_WIF_Fault_Threshold",
            "CAL_WIF_ADC_Min, CAL_WIF_ADC_Max",
        ],
    })
    
    # Diagnostic Requirements
    diagnostic_reqs = pd.DataFrame({
        "Req_ID": [
            "DIAG_WIF_001",
            "DIAG_WIF_002",
            "DIAG_WIF_003",
            "DIAG_WIF_004",
        ],
        "Description": [
            "DTC P242F shall be set when water in fuel filter is detected",
            "DTC P242E shall be set when WIF sensor circuit is open",
            "DTC aging shall require 40 warm-up cycles without fault for DTC clearance",
            "Freeze frame data shall capture WIF sensor resistance at time of fault",
        ],
        "ASIL_Level": [
            "ASIL-A",
            "ASIL-A",
            "QM",
            "QM",
        ],
        "DTC_Code": [
            "P242F",
            "P242E",
            "P242F",
            "P242F",
        ],
        "Calibration_Params": [
            "CAL_WIF_DTC_Debounce",
            "CAL_WIF_Open_Circuit_Threshold",
            "CAL_WIF_Aging_Cycles",
            "CAL_WIF_Freeze_Frame_Config",
        ],
    })
    
    # Calibration Parameters
    calibration_params = pd.DataFrame({
        "Parameter": [
            "CAL_WIF_Resistance_Threshold",
            "CAL_WIF_Warning_Delay",
            "CAL_WIF_DTC_Debounce",
            "CAL_WIF_Critical_Level",
            "CAL_WIF_Reset_Threshold",
            "CAL_WIF_Sample_Rate",
            "CAL_WIF_Debounce_Count",
            "CAL_WIF_Cal_Curve_A",
            "CAL_WIF_Cal_Curve_B",
            "CAL_WIF_CAN_Period",
            "CAL_WIF_Fault_Threshold",
            "CAL_WIF_ADC_Min",
            "CAL_WIF_ADC_Max",
            "CAL_WIF_Open_Circuit_Threshold",
            "CAL_WIF_Aging_Cycles",
            "CAL_WIF_Freeze_Frame_Config",
        ],
        "Unit": [
            "ohms",
            "ms",
            "cycles",
            "ohms",
            "ohms",
            "ms",
            "count",
            "ohms/count",
            "offset",
            "ms",
            "ohms",
            "counts",
            "counts",
            "ohms",
            "cycles",
            "bitmap",
        ],
        "Default_Value": [
            1000,
            200,
            3,
            500,
            5000,
            10,
            5,
            0.1,
            0,
            100,
            800,
            0,
            65535,
            60000,
            40,
            0xFF,
        ],
        "Min": [
            100,
            50,
            1,
            100,
            1000,
            5,
            1,
            0.01,
            -100,
            50,
            100,
            0,
            32768,
            50000,
            1,
            0x00,
        ],
        "Max": [
            10000,
            1000,
            10,
            1000,
            10000,
            100,
            20,
            1.0,
            100,
            500,
            2000,
            1000,
            65535,
            65535,
            100,
            0xFF,
        ],
    })
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        system_reqs.to_excel(writer, sheet_name='System Requirements', index=False)
        software_reqs.to_excel(writer, sheet_name='Software Requirements', index=False)
        diagnostic_reqs.to_excel(writer, sheet_name='Diagnostic Requirements', index=False)
        calibration_params.to_excel(writer, sheet_name='Calibration Parameters', index=False)
    
    print(f"Created sample requirements file: {output_path}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  System Requirements: {len(system_reqs)}")
    print(f"  Software Requirements: {len(software_reqs)}")
    print(f"  Diagnostic Requirements: {len(diagnostic_reqs)}")
    print(f"  Calibration Parameters: {len(calibration_params)}")
    print(f"  Total Requirements: {len(system_reqs) + len(software_reqs) + len(diagnostic_reqs)}")
    
    return output_path


if __name__ == "__main__":
    create_sample_requirements()
