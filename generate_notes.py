"""
Generator and validator for tests/data/annotated_clinical_notes_55.json
Generates 55 highly realistic, clinical specialty-diverse synthetic notes
with verified character-level entity offsets, all 18 HIPAA categories,
and all 9 adversarial challenge axes.
"""

import json
import os
import re
from datetime import datetime, timedelta

def create_note(test_case_id, specialty, note_type, adversarial_tags, segments, date_shift_days=45):
    """
    Construct a clinical note from segments.
    segments: list of tuples:
      - (text, None) -> normal text
      - (text, category, surrogate) -> PHI entity
      - (text, "DATE", surrogate, date_format) -> DATE entity with date shifting
    """
    raw_text_parts = []
    masked_text_parts = []
    entities = []
    
    current_pos = 0
    
    for seg in segments:
        text = seg[0]
        if len(seg) == 2 and seg[1] is None:
            # Normal text
            raw_text_parts.append(text)
            masked_text_parts.append(text)
            current_pos += len(text)
        elif len(seg) >= 3:
            # Entity
            cat = seg[1]
            surrogate = seg[2]
            start = current_pos
            end = start + len(text)
            
            ent_dict = {
                "start": start,
                "end": end,
                "text": text,
                "category": cat,
                "surrogate": surrogate
            }
            
            if cat == "DATE" and len(seg) >= 4 and seg[3]:
                fmt = seg[3]
                try:
                    dt = datetime.strptime(text, fmt)
                    shifted_dt = dt + timedelta(days=date_shift_days)
                    ent_dict["shifted_date"] = shifted_dt.strftime(fmt)
                except Exception:
                    ent_dict["shifted_date"] = text
            
            entities.append(ent_dict)
            raw_text_parts.append(text)
            masked_text_parts.append(surrogate)
            current_pos += len(text)
            
    raw_text = "".join(raw_text_parts)
    expected_masked_text = "".join(masked_text_parts)
    
    # Self-validation of character offsets
    for ent in entities:
        extracted = raw_text[ent["start"]:ent["end"]]
        assert extracted == ent["text"], (
            f"Offset mismatch in {test_case_id}: expected '{ent['text']}', "
            f"got '{extracted}' at [{ent['start']}:{ent['end']}]"
        )
        
    return {
        "test_case_id": test_case_id,
        "specialty": specialty,
        "note_type": note_type,
        "adversarial_tags": adversarial_tags,
        "raw_text": raw_text,
        "entities": entities,
        "expected_masked_text": expected_masked_text,
        "date_shift_days": date_shift_days
    }


def generate_all_55_notes():
    notes = []
    
    # =========================================================================
    # SPECIALTY 1: ONCOLOGY & HEMATOLOGY (6 Notes)
    # =========================================================================
    
    # Note 1: Eponyms (Hodgkin lymphoma vs Dr. Hodgkin) + Relative timeline + Signature
    notes.append(create_note(
        "SYNTH_NOTE_001",
        "Oncology & Hematology",
        "Chemotherapy Consult Note",
        ["eponym_vs_doctor_name", "relative_timeline_preservation", "signatures_headers_footers"],
        [
            ("CLINICAL CONSULTATION NOTE - ONCOLOGY\n", None),
            ("PATIENT NAME: ", None), ("Eleanor Rigby", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("04/12/1974", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ONC-8849201", "MRN", "[MRN_1]"),
            ("\nDATE OF SERVICE: ", None), ("10/15/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING ONCOLOGIST: ", None), ("Dr. Arthur Hodgkin, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1847291045", "LICENSE_NPI", "[NPI_1]"),
            (")\nFACILITY: ", None), ("Memorial Sloan Kettering Cancer Pavilion", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("New York", "GEO_CITY", "[CITY_1]"),
            ("\n\nDIAGNOSIS: Stage IIIB Classic Hodgkin lymphoma (nodular sclerosis subtype).\n", None),
            ("HISTORY OF PRESENT ILLNESS:\nThe patient is a 49-year-old female diagnosed with classic Hodgkin lymphoma following excisional cervical lymph node biopsy on ", None),
            ("09/28/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (". She was evaluated by ", None),
            ("Dr. Hodgkin", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" for initiation of ABVD chemotherapy. Prior PET-CT on ", None),
            ("10/02/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (" demonstrated hypermetabolic mediastinal and supraclavicular lymphadenopathy.\n\n", None),
            ("PLAN:\n1. Cycle 1 Day 1 ABVD infusion scheduled for ", None),
            ("10/22/2023", "DATE", "[DATE_5]", "%m/%d/%Y"),
            (" (7 days post-consultation).\n2. CBC and metabolic panel in 48 hours.\n3. Contact oncology nurse line at ", None),
            ("212-555-0199", "PHONE", "[PHONE_1]"),
            (" or email ", None),
            ("oncology-triage@mskcc.org", "EMAIL", "[EMAIL_1]"),
            (" for fever > 100.4 F.\n\n", None),
            ("Electronically Signed by: ", None),
            ("Arthur Hodgkin, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" on ", None),
            ("10/15/2023 16:45 EDT", "DATE", "[DATE_6]", None)
        ]
    ))
    
    # Note 2: Nicknames, Family Member, Pathology Accession, Burkit lymphoma eponym
    notes.append(create_note(
        "SYNTH_NOTE_002",
        "Oncology & Hematology",
        "Pathology Review & Family Conference",
        ["nicknames_and_aliases", "signatures_headers_footers", "unusual_identifiers_telehealth"],
        [
            ("PATHOLOGY REVIEW & MULTIDISCIPLINARY TUMOR BOARD\n", None),
            ("PATIENT: ", None), ("William 'Billy' Vance", "NAME_PATIENT", "[PATIENT_1]"),
            (" | SSN: ", None), ("948-20-1194", "SSN", "[SSN_1]"),
            (" | ACCESSION #: ", None), ("PATH-2023-99841", "ID_ACCESSION", "[ACCESSION_1]"),
            ("\nSPECIMEN DATE: ", None), ("11/04/2023", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nHOSPITAL: ", None), ("Dana-Farber Cancer Institute", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Boston", "GEO_CITY", "[CITY_1]"),
            (" | ZIP: ", None), ("02215", "GEO_ZIP", "[ZIP_1]"),
            ("\nPATHOLOGIST: ", None), ("Dr. Sarah Burkitt-Lee, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nFAMILY ATTENDEES: Mother ", None),
            ("Patricia Vance", "NAME_FAMILY", "[FAMILY_1]"),
            (" (legal guardian) and uncle ", None),
            ("Robert 'Bob' Vance", "NAME_FAMILY", "[FAMILY_2]"),
            (".\n\nFINDINGS:\nBone marrow aspirate and core biopsy confirm high-grade B-cell Burkitt lymphoma with MYC translocation t(8;14). Note that patient Burkitt lymphoma status was reviewed directly with Dr. Burkitt-Lee.\n\n", None),
            ("FINANCIAL COUNSELING: Medicaid ID: ", None),
            ("MED-88492014A", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            (". Billing Guarantor Account: ", None),
            ("ACT-902841", "ACCOUNT", "[ACCOUNT_1]"),
            (".\nEmergency Contact Phone: ", None),
            ("617-555-0842", "PHONE", "[PHONE_1]"),
            ("\n\nReview Completed by: ", None),
            ("Dr. Sarah Burkitt-Lee, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 3: Whipple procedure eponym vs Dr. Whipple, Table format, Address
    notes.append(create_note(
        "SYNTH_NOTE_003",
        "Oncology & Hematology",
        "Surgical Oncology Operative Summary",
        ["eponym_vs_doctor_name", "tables_and_flowsheets", "signatures_headers_footers"],
        [
            ("SURGICAL ONCOLOGY OPERATIVE REPORT\n", None),
            ("PATIENT: ", None), ("Margaret Thorne", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("08/23/1961", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("7749201", "MRN", "[MRN_1]"),
            ("\nSURGEON: ", None), ("Dr. Gregory Whipple, MD, FACS", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | ASSISTANT: ", None), ("Dr. Clara Barton, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nLOCATION: ", None), ("750 Longwood Ave", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Boston", "GEO_CITY", "[CITY_1]"),
            (", MA ", None), ("02115", "GEO_ZIP", "[ZIP_1]"),
            ("\nDATE OF SURGERY: ", None), ("09/14/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\n\nPROCEDURE PERFORMED: Pancreaticoduodenectomy (Whipple procedure) with pylorus preservation.\n", None),
            ("INDICATION: Pancreatic adenocarcinoma of the head of the pancreas.\n\nOPERATIVE TABLE LOG:\n", None),
            ("| TIME | STEP | OPERATOR | FINDINGS |\n", None),
            ("| 08:00 | Incision | ", None), ("Dr. Whipple", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | Subcostal bilateral incision |\n", None),
            ("| 09:30 | Resection | ", None), ("Dr. Whipple", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | Resection of pancreatic head and duodenum (Whipple specimen) |\n", None),
            ("| 12:15 | Reconstruction | ", None), ("Dr. Barton", "NAME_PROVIDER", "[PROVIDER_2]"),
            (" | Pancreaticojejunostomy and choledochojejunostomy |\n\n", None),
            ("POST-OP PLAN: ICU admission under care of ", None),
            ("Dr. Whipple", "NAME_PROVIDER", "[PROVIDER_1]"),
            (". Drain output monitoring daily.\nDictated by: ", None),
            ("Gregory Whipple, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | Transcriptionist: ", None),
            ("Karen Miller", "NAME_PROVIDER", "[PROVIDER_3]")
        ]
    ))
    
    # Note 4: Raynaud's phenomenon & Kaposi's sarcoma eponyms, Clinical Trial ID, DEA #
    notes.append(create_note(
        "SYNTH_NOTE_004",
        "Oncology & Hematology",
        "Hematology Clinical Trial Enrollment",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("CLINICAL TRIAL ENROLLMENT NOTE\n", None),
            ("SUBJECT ID: ", None), ("CT-ONC-2023-882", "ID_ACCESSION", "[ID_1]"),
            (" | PATIENT: ", None), ("David A. Copperfield", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("12/03/1978", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nPRINCIPAL INVESTIGATOR: ", None), ("Dr. Rachel Raynaud, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (DEA: ", None), ("BR8492014", "LICENSE_DEA", "[LICENSE_1]"),
            (")\nSITE: ", None), ("Fred Hutchinson Cancer Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Seattle", "GEO_CITY", "[CITY_1]"),
            (", King County\n", None),
            ("ENROLLMENT DATE: ", None), ("07/19/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\n\nMEDICAL HISTORY:\nPatient has concomitant secondary Raynaud's phenomenon and history of cutaneous Kaposi's sarcoma. Examined by ", None),
            ("Dr. Raynaud", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" who confirmed Raynaud's phenomenon symptoms are stable under nifedipine.\n\n", None),
            ("TRIAL PROTOCOL:\nAdminister investigational monoclonal antibody CAR-T infusion on ", None),
            ("08/02/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (14 days post-enrollment).\nEmergency Protocol Contact: ", None),
            ("206-555-0144", "PHONE", "[PHONE_1]"),
            (" | Secure Fax: ", None),
            ("206-555-0188", "FAX", "[FAX_1]"),
            ("\nSigned: ", None),
            ("Rachel Raynaud, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 5: Misspellings/OCR Typos in Oncology note, License Plate, Insurance ID
    notes.append(create_note(
        "SYNTH_NOTE_005",
        "Oncology & Hematology",
        "Outpatient Infusion Center Progress Note",
        ["typos_and_phonetic_misspellings", "mixed_formatting_and_delimiters"],
        [
            ("INFUSION CNTR PROGRSS NOTE\n", None),
            ("Pateint: ", None), ("Theresa M. O'Conner", "NAME_PATIENT", "[PATIENT_1]"),
            (" | MR#: ", None), ("MRN-0092834", "MRN", "[MRN_1]"),
            (" | Insurnce Policy: ", None), ("BCBS-9948201A", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nAttnding Oncolgist: ", None), ("Dr. Jonathon Smyth, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | Nurse: ", None), ("Brenda K. Walsh, RN", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nDate of Trtment: ", None), ("06/21/2023", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nClinic Address: ", None), ("1204 Blossom Hill Road, Suite 300", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("San Jose", "GEO_CITY", "[CITY_1]"),
            (", CA ", None), ("95123", "GEO_ZIP", "[ZIP_1]"),
            ("\nPatient Vehicle Plate: ", None), ("CA 7XYZ892", "VEHICLE", "[VEHICLE_1]"),
            ("\n\nPROGRESS SUMMERY:\nMrs. O'Conner tolerated paclitaxel and carboplatin infusion well without acute anaphalaxis. Reviewed by Dr. Smyth.\nFollow up scheduled for ", None),
            ("07/12/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            (".\nContact callback: ", None),
            ("408-555-0177", "PHONE", "[PHONE_1]")
        ]
    ))
    
    # Note 6: Radiation Oncology, DICOM Photo, Device Serial
    notes.append(create_note(
        "SYNTH_NOTE_006",
        "Oncology & Hematology",
        "Radiation Oncology Simulation & Setup Note",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("RADIATION ONCOLOGY SIMULATION NOTE\n", None),
            ("PATIENT: ", None), ("Samuel L. Jackson-Vance", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("03/15/1966", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("RAD-883921", "MRN", "[MRN_1]"),
            ("\nDATE OF SIMULATION: ", None), ("05/18/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nRADIATION ONCOLOGIST: ", None), ("Dr. Evelyn Reed, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nFACILITY: ", None), ("Stanford Health Care Radiation Pavilion", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Palo Alto", "GEO_CITY", "[CITY_1]"),
            ("\n\nSIMULATION DETAILS:\nPatient immobilized with thermoplastic mask. CT simulation reference photo: ", None),
            ("facial_setup_photo_pat883921.dcm", "PHOTO", "[PHOTO_1]"),
            (".\nLinear Accelerator: Varian TrueBeam SN: ", None),
            ("TB-99482-X", "DEVICE", "[DEVICE_1]"),
            (".\nPrescription: 60 Gy in 30 fractions to head and neck planning target volume (PTV).\n\n", None),
            ("Physician Signature: ", None),
            ("Evelyn Reed, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None),
            ("1992837461", "LICENSE_NPI", "[NPI_1]"),
            (")")
        ]
    ))

    # =========================================================================
    # SPECIALTY 2: CARDIOLOGY & CARDIOTHORACIC SURGERY (6 Notes)
    # =========================================================================
    
    # Note 7: Pacemaker implant SN, UDI, Purkinje / Bundle of His eponyms vs Dr. His
    notes.append(create_note(
        "SYNTH_NOTE_007",
        "Cardiology & Cardiothoracic Surgery",
        "Electrophysiology Pacemaker Implantation Operative Note",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("CARDIOLOGY ELECTROPHYSIOLOGY OPERATIVE REPORT\n", None),
            ("PATIENT: ", None), ("Charles 'Chuck' Montgomery", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("11/30/1952", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("CARD-992014", "MRN", "[MRN_1]"),
            ("\nPROCEDURE DATE: ", None), ("08/14/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nELECTROPHYSIOLOGIST: ", None), ("Dr. Wilhelm His-Bernard, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | FELLOW: ", None), ("Dr. Anita Patel, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nHOSPITAL: ", None), ("Cleveland Clinic Foundation", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Cleveland", "GEO_CITY", "[CITY_1]"),
            (", ", None), ("Cuyahoga County", "GEO_COUNTY", "[COUNTY_1]"),
            (", OH ", None), ("44195", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPROCEDURE: Permanent Dual-Chamber Pacemaker Implantation.\n", None),
            ("INDICATION: High-grade AV block with conduction disease involving the Bundle of His and Purkinje fibers.\n\n", None),
            ("DEVICE IMPLANTED:\nGenerator: Medtronic Azure XT DR, Model W1TR01, SN: ", None),
            ("PAC-99482014-H", "DEVICE", "[DEVICE_1]"),
            ("\nUDI: ", None),
            ("(01)00643169007222(17)250101(10)LOT982", "DEVICE", "[DEVICE_2]"),
            ("\nRight Atrial Lead SN: ", None),
            ("RAL-8849201", "DEVICE", "[DEVICE_3]"),
            (" | Right Ventricular Lead SN: ", None),
            ("RVL-8849202", "DEVICE", "[DEVICE_4]"),
            ("\n\nINTRAOPERATIVE NOTES:\nMapping of the Bundle of His was performed by Dr. His-Bernard. Satisfactory pacing thresholds obtained without diaphragmatic stimulation.\n\n", None),
            ("DISCHARGE & FOLLOW-UP:\nRemote monitoring portal: ", None),
            ("https://carelink.clevelandclinic.org/patient/992014", "URL", "[URL_1]"),
            ("\nCallback clinic: ", None),
            ("216-555-0122", "PHONE", "[PHONE_1]"),
            (" | Fax: ", None),
            ("216-555-0123", "FAX", "[FAX_1]"),
            ("\nSigned: ", None),
            ("Wilhelm His-Bernard, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 8: Swan-Ganz catheter, Cardiac Cath Table, Multi-date relative interval
    notes.append(create_note(
        "SYNTH_NOTE_008",
        "Cardiology & Cardiothoracic Surgery",
        "Right Heart Catheterization & Hemodynamics Report",
        ["eponym_vs_doctor_name", "tables_and_flowsheets", "relative_timeline_preservation"],
        [
            ("CARDIAC CATHETERIZATION HEMODYNAMICS REPORT\n", None),
            ("PATIENT: ", None), ("Gloria Henderson", "NAME_PATIENT", "[PATIENT_1]"),
            (" | MRN: ", None), ("CATH-448201", "MRN", "[MRN_1]"),
            (" | DOB: ", None), ("02/17/1960", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nADMISSION DATE: ", None), ("09/10/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            (" | PROCEDURE DATE: ", None), ("09/12/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            ("\nINTERVENTIONAL CARDIOLOGIST: ", None), ("Dr. Jeremy Swan, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nINSTITUTION: ", None), ("Texas Heart Institute", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Houston", "GEO_CITY", "[CITY_1]"),
            (", TX ", None), ("77030", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nHEMODYNAMIC DATA LOG:\n", None),
            ("| MEASUREMENT | VALUE | NORMAL RANGE |\n", None),
            ("| RA Pressure | 14 mmHg | 2-6 mmHg |\n", None),
            ("| RV Pressure | 48/12 mmHg | 15-30/2-8 mmHg |\n", None),
            ("| PA Pressure (Mean) | 36 mmHg | 10-20 mmHg |\n", None),
            ("| PCWP (Wedge) | 22 mmHg | 6-12 mmHg |\n", None),
            ("| Cardiac Output (Thermodilution) | 3.4 L/min | 4.0-8.0 L/min |\n\n", None),
            ("NARRATIVE: Placement of a 7-French Swan-Ganz catheter via right internal jugular vein. Dr. Swan noted severe pulmonary hypertension secondary to left heart failure. Two days after admission (procedure day 09/12/2023), IV milrinone was initiated.\nPlanned discharge on ", None),
            ("09/16/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (" (6 days post-admission).\nProvider Contact: ", None),
            ("713-555-0188", "PHONE", "[PHONE_1]"),
            ("\nElectronically Signed: ", None),
            ("Jeremy Swan, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 9: Heart Failure, MBI Medicare ID, Nickname, Address
    notes.append(create_note(
        "SYNTH_NOTE_009",
        "Cardiology & Cardiothoracic Surgery",
        "Heart Failure Clinic Progress Note",
        ["nicknames_and_aliases", "signatures_headers_footers"],
        [
            ("HEART FAILURE CLINICAL PROGRESS NOTE\n", None),
            ("PATIENT: ", None), ("Harold 'Hal' Jenkins", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("07/04/1948", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MEDICARE MBI: ", None), ("1EG4-TE5-MK72", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nDATE: ", None), ("10/05/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nCARDIOLOGIST: ", None), ("Dr. Rebecca Vance-Sterling, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | NURSE PRACTITIONER: ", None), ("Linda Gomez, NP", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nHOME ADDRESS: ", None), ("405 Whispering Pines Dr, Apt 2C", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Atlanta", "GEO_CITY", "[CITY_1]"),
            (", ", None), ("Fulton County", "GEO_COUNTY", "[COUNTY_1]"),
            (", GA ", None), ("30308", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nASSESSMENT: HFrEF with NYHA Class III symptoms, EF 28%. Patient Hal Jenkins reports improved orthopnea on Entresto.\n", None),
            ("PLAN:\n1. Increase sacubitril/valsartan to 49/51 mg BID.\n2. Serum Cr and K+ draw in 1 week on ", None),
            ("10/12/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\n3. Clinic callback: ", None),
            ("404-555-0133", "PHONE", "[PHONE_1]"),
            (" | Email: ", None),
            ("hal.jenkins48@gmail.com", "EMAIL", "[EMAIL_1]"),
            ("\nSigned: ", None),
            ("Rebecca Vance-Sterling, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 10: CABG Operative Report, Complex signatures, Lot number
    notes.append(create_note(
        "SYNTH_NOTE_010",
        "Cardiology & Cardiothoracic Surgery",
        "Coronary Artery Bypass Operative Record",
        ["signatures_headers_footers", "unusual_identifiers_telehealth"],
        [
            ("CARDIOTHORACIC SURGERY OPERATIVE RECORD\n", None),
            ("PATIENT: ", None), ("Anthony Russo", "NAME_PATIENT", "[PATIENT_1]"),
            (" | MRN: ", None), ("CTS-002941", "MRN", "[MRN_1]"),
            (" | HAR: ", None), ("HAR-9948201", "ACCOUNT", "[ACCOUNT_1]"),
            ("\nSURGERY DATE: ", None), ("06/14/2023", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nATTENDING SURGEON: ", None), ("Dr. Salvatore DeBakey-Torres, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1487920145", "LICENSE_NPI", "[NPI_1]"),
            (")\nPERFUSIONIST: ", None), ("Mark Alvarez, CCP", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nFACILITY: ", None), ("Northwestern Memorial Hospital", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Chicago", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60611", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPROCEDURE: Coronary artery bypass grafting x3 (LIMA to LAD, SVG to OM1, SVG to PDA).\n", None),
            ("Cannula Lot #: ", None),
            ("LOT-CAN-2023-88", "DEVICE", "[DEVICE_1]"),
            (".\nCross-clamp time: 58 minutes. Cardiopulmonary bypass time: 74 minutes.\nPatient transferred to CVICU under care of Dr. DeBakey-Torres.\n\n", None),
            ("Dictated by: ", None),
            ("Salvatore DeBakey-Torres, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | Transcribed on: ", None),
            ("06/14/2023 20:15", "DATE", "[DATE_2]", None)
        ]
    ))
    
    # Note 11: Echocardiography Report, State License, Emergency contact phone
    notes.append(create_note(
        "SYNTH_NOTE_011",
        "Cardiology & Cardiothoracic Surgery",
        "Transthoracic Echocardiogram Report",
        ["mixed_formatting_and_delimiters", "signatures_headers_footers"],
        [
            ("ECHOCARDIOGRAPHY LABORATORY REPORT\n", None),
            ("PATIENT: ", None), ("Beatrice Kowalski", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("09/08/1955", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ECHO-88401", "MRN", "[MRN_1]"),
            ("\nEXAM DATE: ", None), ("04/05/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nSONOGRAPHER: ", None), ("Jessica Lee, RDCS", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | INTERPRETING PHYSICIAN: ", None), ("Dr. Frank Sterling, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            (" (License: ", None), ("MD-IL-049281", "LICENSE_STATE", "[LICENSE_1]"),
            (")\nEMERGENCY CONTACT: Daughter ", None),
            ("Karen Kowalski-Smith", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("312-555-0166", "PHONE", "[PHONE_1]"),
            (")\n\nFINDINGS:\n1. Severe aortic stenosis with peak velocity 4.4 m/s and mean gradient 42 mmHg.\n2. Preserved LV ejection fraction 60%.\n3. Concentric left ventricular hypertrophy.\n\nTransmitted to referring physician Dr. Frank Sterling.\nReport Hash: ", None),
            ("EC-994820148", "ID_ACCESSION", "[ID_1]")
        ]
    ))
    
    # Note 12: Cardiac Rehabilitation, VIN, Web Portal, Relative intervals
    notes.append(create_note(
        "SYNTH_NOTE_012",
        "Cardiology & Cardiothoracic Surgery",
        "Phase II Cardiac Rehabilitation Intake",
        ["unusual_identifiers_telehealth", "relative_timeline_preservation"],
        [
            ("CARDIAC REHABILITATION INTAKE EVALUATION\n", None),
            ("PATIENT: ", None), ("Raymond 'Ray' Martinez", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("01/22/1963", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("REHAB-9921", "MRN", "[MRN_1]"),
            ("\nINTAKE DATE: ", None), ("05/01/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nCLINICAL EXERCISE PHYSIOLOGIST: ", None), ("Tyler Brooks, MS, CEP", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nSUPERVISING CARDIOLOGIST: ", None), ("Dr. Nathan Chen, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nPATIENT VEHICLE VIN: ", None), ("1HGCR2F83HA029481", "VEHICLE", "[VEHICLE_1]"),
            ("\n\nCLINICAL TIMELINE:\nPatient suffered NSTEMI on ", None),
            ("04/01/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (". Underwent PCI with drug-eluting stent to LAD on ", None),
            ("04/02/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (" (1 day post-infarct). Now 30 days post-event initiating 12-week rehab protocol.\nPatient Portal Login: ", None),
            ("https://rehab.myhealthportal.com/user/rmartinez63", "URL", "[URL_1]"),
            ("\nEmergency contact: ", None),
            ("Elena Martinez", "NAME_FAMILY", "[FAMILY_1]"),
            (" at ", None),
            ("312-555-0192", "PHONE", "[PHONE_1]"),
            ("\nSignature: ", None),
            ("Tyler Brooks, MS, CEP", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 3: NEUROLOGY & NEUROSURGERY (6 Notes)
    # =========================================================================
    
    # Note 13: Parkinson's disease vs Dr. Parkinson, Babinski reflex vs Dr. Babinski
    notes.append(create_note(
        "SYNTH_NOTE_013",
        "Neurology & Neurosurgery",
        "Movement Disorders Neurological Evaluation",
        ["eponym_vs_doctor_name", "signatures_headers_footers"],
        [
            ("NEUROLOGICAL CONSULTATION REPORT\n", None),
            ("PATIENT: ", None), ("Arthur Pendelton", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("05/19/1956", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("NEUR-884910", "MRN", "[MRN_1]"),
            ("\nCONSULT DATE: ", None), ("10/18/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nNEUROLOGIST: ", None), ("Dr. James Parkinson-White, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | RESIDENT: ", None), ("Dr. Joseph Babinski-Reed, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nCLINIC: ", None), ("Johns Hopkins Comprehensive Movement Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Baltimore", "GEO_CITY", "[CITY_1]"),
            (", MD ", None), ("21287", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nEXAMINATION & FINDINGS:\nPhysical exam conducted by Dr. Babinski-Reed. Plantar response: Babinski reflex is flexor bilaterally (negative Babinski sign). Resting cogwheel rigidity and bradykinesia noted in right upper extremity.\n", None),
            ("IMPRESSION: Idiopathic Parkinson's disease, Hoehn and Yahr Stage II. Evaluated by ", None),
            ("Dr. Parkinson-White", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" who confirmed the diagnosis of Parkinson's disease.\n\nPLAN:\n1. Ropinirole titration.\n2. Follow-up in 8 weeks on ", None),
            ("12/13/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact clinic at ", None),
            ("410-555-0144", "PHONE", "[PHONE_1]"),
            (" | Email: ", None),
            ("jparkinson@jhmi.edu", "EMAIL", "[EMAIL_1]"),
            ("\nSigned: ", None),
            ("James Parkinson-White, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 14: Alzheimer's dementia vs Dr. Alzheimer, Bell's palsy vs Dr. Bell, Relative dates
    notes.append(create_note(
        "SYNTH_NOTE_014",
        "Neurology & Neurosurgery",
        "Cognitive Behavioral Neurology Consult",
        ["eponym_vs_doctor_name", "relative_timeline_preservation"],
        [
            ("COGNITIVE NEUROLOGY CONSULTATION\n", None),
            ("PATIENT: ", None), ("Constance 'Connie' Miller", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("10/11/1945", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("COG-77402", "MRN", "[MRN_1]"),
            ("\nEVALUATION DATE: ", None), ("07/14/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING NEUROLOGIST: ", None), ("Dr. Alois Alzheimer-Scott, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | FELLOW: ", None), ("Dr. Charles Bell, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nINFORMANT: Daughter ", None),
            ("Nancy Miller-Davis", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("206-555-0199", "PHONE", "[PHONE_1]"),
            (")\n\nHISTORY & PHYSICAL:\nPatient evaluated for progressive memory decline. MMSE score 19/30. Dr. Alzheimer-Scott reviewed brain MRI showing bilateral hippocampal atrophy consistent with early Alzheimer's disease.\nAdditionally, patient has residual left facial weakness from previous Bell's palsy diagnosed 3 years ago; Dr. Bell noted facial symmetry is stable.\n\n", None),
            ("CHRONOLOGY: Memory complaints started around ", None),
            ("01/10/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (6 months prior). Repeat cognitive battery scheduled in 6 months on ", None),
            ("01/14/2024", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (".\nProvider Signature: ", None),
            ("Alois Alzheimer-Scott, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 15: Acute Ischemic Stroke, Circle of Willis, Rapid timestamps, NPI
    notes.append(create_note(
        "SYNTH_NOTE_015",
        "Neurology & Neurosurgery",
        "Acute Stroke Code & Endovascular Thrombectomy Note",
        ["eponym_vs_doctor_name", "signatures_headers_footers", "tables_and_flowsheets"],
        [
            ("COMPREHENSIVE STROKE CENTER EMERGENCY RECORD\n", None),
            ("PATIENT: ", None), ("Derrick Vance", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("06/25/1971", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("STRK-0091", "MRN", "[MRN_1]"),
            ("\nENCOUNTER DATE: ", None), ("11/02/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nVASCULAR NEUROLOGIST: ", None), ("Dr. Thomas Willis, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1679201485", "LICENSE_NPI", "[NPI_1]"),
            (")\nINTERVENTIONAL NEURORADIOLOGIST: ", None), ("Dr. Karen Vance, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\n\nSTROKE CODE TIMELINE:\n", None),
            ("| TIME | EVENT | NOTES |\n", None),
            ("| 14:10 | Last Known Well | Witnessed by spouse ", None),
            ("Susan Vance", "NAME_FAMILY", "[FAMILY_1]"),
            (" |\n| 14:45 | ED Arrival | NIHSS 18 |\n", None),
            ("| 15:00 | CTA Head/Neck | Left M1 occlusion in Circle of Willis |\n", None),
            ("| 15:20 | IV TNK Thrombolysis | Administered by ", None),
            ("Dr. Willis", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" |\n| 15:45 | Groin Puncture | Thrombectomy initiated by ", None),
            ("Dr. Karen Vance", "NAME_PROVIDER", "[PROVIDER_2]"),
            (" |\n| 16:10 | Revascularization | TICI 3 recanalization of Circle of Willis branches |\n\n", None),
            ("TRANSCRIPTION NOTE: Dictated by ", None),
            ("Thomas Willis, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" on ", None),
            ("11/02/2023 18:00", "DATE", "[DATE_3]", None)
        ]
    ))
    
    # Note 16: Spine Surgery Post-Op, Implants UDI, Romberg test
    notes.append(create_note(
        "SYNTH_NOTE_016",
        "Neurology & Neurosurgery",
        "Neurosurgical Spine Post-Operative Note",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth"],
        [
            ("NEUROSURGERY SPINE POST-OP PROGRESS NOTE\n", None),
            ("PATIENT: ", None), ("Gerald 'Gerry' Fitzgerald", "NAME_PATIENT", "[PATIENT_1]"),
            (" | MRN: ", None), ("NS-88402", "MRN", "[MRN_1]"),
            (" | DOB: ", None), ("03/30/1965", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nPOST-OP DAY 2: ", None), ("08/19/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            (" (Surgery Date: ", None), ("08/17/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (")\nNEUROSURGEON: ", None), ("Dr. Moritz Romberg-Taylor, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nFACILITY: ", None), ("Barrow Neurological Institute", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Phoenix", "GEO_CITY", "[CITY_1]"),
            (", AZ ", None), ("85013", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPROCEDURE: L4-L5 Lumbar Laminectomy and Instrumented Fusion.\nPedicle Screw Lot: ", None),
            ("LOT-SPINE-9948", "DEVICE", "[DEVICE_1]"),
            (" | PEEK Cage SN: ", None),
            ("SN-PEEK-004821", "DEVICE", "[DEVICE_2]"),
            ("\n\nEXAM: Sensation intact to light touch. Romberg test postponed until full ambulation. Dr. Romberg-Taylor confirmed no CSF leak.\nDischarge planned for post-op day 4 on ", None),
            ("08/21/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (".\nContact nurse line: ", None),
            ("602-555-0177", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Moritz Romberg-Taylor, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 17: Guillain-Barré syndrome & Horner's syndrome, Telehealth Zoom, IP
    notes.append(create_note(
        "SYNTH_NOTE_017",
        "Neurology & Neurosurgery",
        "Neurology Telemedicine Follow-Up",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth"],
        [
            ("TELEHEALTH NEUROLOGY CONSULTATION NOTE\n", None),
            ("PATIENT: ", None), ("Valerie Higgins", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("12/04/1982", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("TELE-94820", "MRN", "[MRN_1]"),
            ("\nSESSION DATE: ", None), ("09/25/2023 11:00 UTC", "DATE", "[DATE_2]", None),
            ("\nPROVIDER: ", None), ("Dr. Johann Horner, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nTELEHEALTH SESSION URL: ", None),
            ("https://telehealth.jhmi.edu/v/room-8849201", "URL", "[URL_1]"),
            ("\nCLIENT IP ADDRESS: ", None),
            ("198.51.100.42", "IP", "[IP_1]"),
            ("\n\nCLINICAL NOTE:\nFollow-up evaluation for patient recovering from Guillain-Barré syndrome and mild right-sided Horner's syndrome. Dr. Horner conducted motor examination via high-definition video feed.\nPatient reports significant resolution of ascending weakness following IVIG therapy in ", None),
            ("08/2023", "DATE", "[DATE_3]", None),
            (".\nFollow-up via portal: ", None),
            ("https://mychart.hopkins.org/pat/valerie_higgins", "URL", "[URL_2]"),
            ("\nCallback: ", None),
            ("410-555-0182", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Johann Horner, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 18: EEG Report, Tourette syndrome vs Dr. Tourette, Driver's License
    notes.append(create_note(
        "SYNTH_NOTE_018",
        "Neurology & Neurosurgery",
        "Routine Electroencephalogram (EEG) Report",
        ["eponym_vs_doctor_name", "signatures_headers_footers"],
        [
            ("CLINICAL NEUROPHYSIOLOGY EEG REPORT\n", None),
            ("PATIENT: ", None), ("Lucas 'Luke' Skywalker-Smith", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("04/15/2005", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("EEG-449102", "MRN", "[MRN_1]"),
            (" | DRIVER LICENSE: ", None), ("DL-MD-88392014", "LICENSE_STATE", "[LICENSE_1]"),
            ("\nRECORDING DATE: ", None), ("10/09/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nINTERPRETING EPILEPTOLOGIST: ", None), ("Dr. Georges Gilles-Tourette, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nREFERRING PHYSICIAN: ", None), ("Dr. Amanda Clarke, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\n\nHISTORY: 18-year-old male with history of motor and vocal tics consistent with Tourette syndrome and new-onset unprovoked seizure.\n", None),
            ("EEG FINDINGS:\nNormal background with 9.5 Hz posterior dominant rhythm. No epileptiform discharges or photosensitive paroxysms recorded during hyperventilation. Reviewed by ", None),
            ("Dr. Gilles-Tourette", "NAME_PROVIDER", "[PROVIDER_1]"),
            (".\n\nSigned: ", None),
            ("Georges Gilles-Tourette, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None),
            ("1992830192", "LICENSE_NPI", "[NPI_1]"),
            (")")
        ]
    ))

    # =========================================================================
    # SPECIALTY 4: PEDIATRICS & NEONATOLOGY (NICU) (5 Notes)
    # =========================================================================
    
    # Note 19: NICU Discharge, Apgar score, Mother/Father names, Pediatric dates
    notes.append(create_note(
        "SYNTH_NOTE_019",
        "Pediatrics & Neonatology",
        "NICU Discharge Summary",
        ["eponym_vs_doctor_name", "signatures_headers_footers", "relative_timeline_preservation"],
        [
            ("NEONATAL INTENSIVE CARE UNIT DISCHARGE SUMMARY\n", None),
            ("INFANT: ", None), ("Baby Boy Jackson (Liam Jackson)", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("09/01/2023 04:12", "DATE", "[DATE_1]", None),
            (" | DISCHARGE: ", None), ("10/10/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("NICU-88492", "MRN", "[MRN_1]"),
            (" | BIRTH WEIGHT: 1420 grams (31 weeks gestational age)\n", None),
            ("MOTHER: ", None), ("Jennifer Jackson", "NAME_FAMILY", "[FAMILY_1]"),
            (" | FATHER: ", None), ("Michael Jackson", "NAME_FAMILY", "[FAMILY_2]"),
            ("\nATTENDING NEONATOLOGIST: ", None), ("Dr. Virginia Apgar-Stevens, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nHOSPITAL: ", None), ("Texas Children's Hospital", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Houston", "GEO_CITY", "[CITY_1]"),
            (", TX ", None), ("77030", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nBIRTH HISTORY:\nInfant delivered via emergency C-section. Apgar score was 4 at 1 minute and 8 at 5 minutes. Dr. Apgar-Stevens noted respiratory distress syndrome requiring surfactant on day 1 (09/01/2023).\n\n", None),
            ("HOSPITAL COURSE:\nCaffeine therapy discontinued on day 30 (10/01/2023). Infant reached full oral feeds on day 35 (10/06/2023). Cleared for home discharge after 39 days in NICU.\nPediatrician follow-up with ", None),
            ("Dr. Timothy Ross, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            (" on ", None),
            ("10/14/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nParent Phone: ", None),
            ("713-555-0133", "PHONE", "[PHONE_1]"),
            (" | Mother Email: ", None),
            ("jennifer.jackson89@gmail.com", "EMAIL", "[EMAIL_1]"),
            ("\nSigned: ", None),
            ("Virginia Apgar-Stevens, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 20: Well-Child Check, School Name/Address, Nickname, Vaccine Dates
    notes.append(create_note(
        "SYNTH_NOTE_020",
        "Pediatrics & Neonatology",
        "Pediatric Well-Child Visit",
        ["nicknames_and_aliases", "mixed_formatting_and_delimiters"],
        [
            ("PEDIATRIC OUTPATIENT CLINIC NOTE\n", None),
            ("PATIENT: ", None), ("Samantha 'Sammie' Jenkins", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("05/12/2017", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("PED-99281", "MRN", "[MRN_1]"),
            ("\nVISIT DATE: ", None), ("05/18/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            (" (6-Year Well-Child Check)\n", None),
            ("PEDIATRICIAN: ", None), ("Dr. Laura Ingalls, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nGUARDIAN: Mother ", None),
            ("Rebecca Jenkins", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Cell: ", None),
            ("312-555-0149", "PHONE", "[PHONE_1]"),
            (")\nSCHOOL: ", None),
            ("Lincoln Elementary School", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Oak Park", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60302", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nDEVELOPMENT & IMMUNIZATIONS:\nSammie is thriving in kindergarten. Vitals: Ht 46 inches, Wt 48 lbs (60th percentile).\nAdministered DTaP and IPV booster on 05/18/2023.\nInsurance Member ID: ", None),
            ("BCBS-PED-88392", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nFollow-up in 1 year on ", None),
            ("05/18/2024", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nProvider Signature: ", None),
            ("Laura Ingalls, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 21: Pediatric Cardiology, Kawasaki disease eponym, Device SN, Medicaid
    notes.append(create_note(
        "SYNTH_NOTE_021",
        "Pediatrics & Neonatology",
        "Pediatric Cardiology Consult",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth"],
        [
            ("PEDIATRIC CARDIOLOGY CONSULTATION\n", None),
            ("PATIENT: ", None), ("Benjamin 'Benny' Clark", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("11/08/2019", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("PCARD-44820", "MRN", "[MRN_1]"),
            (" | MEDICAID ID: ", None), ("MCD-IL-9948201", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nCONSULT DATE: ", None), ("07/22/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING CARDIOLOGIST: ", None), ("Dr. Tomisaku Kawasaki-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nHOSPITAL: ", None), ("Ann & Robert H. Lurie Children's Hospital", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Chicago", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60611", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nHISTORY: 3-year-old male with persistent fever, strawberry tongue, and cervical lymphadenopathy. Evaluated by Dr. Kawasaki-Miller and diagnosed with classic Kawasaki disease.\n", None),
            ("ECHO FINDINGS: Echocardiogram SN: ", None),
            ("ECHO-PROBE-4491", "DEVICE", "[DEVICE_1]"),
            (" demonstrated normal coronary artery dimensions without aneurysm formation.\n\nPLAN:\n1. IVIG infusion (2 g/kg) and high-dose aspirin.\n2. Repeat echo in 2 weeks on ", None),
            ("08/05/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nEmergency contact: Father ", None),
            ("David Clark", "NAME_FAMILY", "[FAMILY_1]"),
            (" at ", None),
            ("312-555-0184", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Tomisaku Kawasaki-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 22: Pediatric Genetics, Dysmorphology, Barcode, Microarray ID
    notes.append(create_note(
        "SYNTH_NOTE_022",
        "Pediatrics & Neonatology",
        "Clinical Genetics Dysmorphology Evaluation",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("CLINICAL GENETICS CONSULTATION NOTE\n", None),
            ("PATIENT: ", None), ("Maya Lin-Rodriguez", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("03/14/2021", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("GEN-88391", "MRN", "[MRN_1]"),
            ("\nDATE OF EVALUATION: ", None), ("09/19/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nMEDICAL GENETICIST: ", None), ("Dr. Helena Vogel, MD, PhD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1884920194", "LICENSE_NPI", "[NPI_1]"),
            (")\nGENETIC COUNSELOR: ", None), ("Sarah Jenkins, MS, CGC", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nSPECIMEN BARCODE: ", None), ("BARCODE-DNA-9948210", "ID_ACCESSION", "[ID_1]"),
            ("\nCHROMOSOMAL MICROARRAY ID: ", None), ("CMA-2023-7741", "ID_ACCESSION", "[ID_2]"),
            ("\n\nCLINICAL SUMMARY:\nEvaluated for developmental delay and subtle dysmorphic facial features. Microarray sent to Quest Diagnostics on ", None),
            ("09/20/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nMother ", None),
            ("Elena Rodriguez", "NAME_FAMILY", "[FAMILY_1]"),
            (" and Father ", None),
            ("Tony Lin", "NAME_FAMILY", "[FAMILY_2]"),
            (" consented for trio Whole Exome Sequencing.\nPortal access: ", None),
            ("https://genetics.pediatrix.org/portal/pat_maya88", "URL", "[URL_1]"),
            ("\nCallback: ", None),
            ("415-555-0193", "PHONE", "[PHONE_1]"),
            ("\nSignature: ", None),
            ("Helena Vogel, MD, PhD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 23: Pediatric Asthma Allergy, Typos in note, Street Address, SSN
    notes.append(create_note(
        "SYNTH_NOTE_023",
        "Pediatrics & Neonatology",
        "Pediatric Allergy & Immunology Progress Note",
        ["typos_and_phonetic_misspellings", "mixed_formatting_and_delimiters"],
        [
            ("PEDIATRC ALLRGY & IMMUNOLOGY NOTE\n", None),
            ("Pateint: ", None), ("Jonathan 'Jonny' Braverman", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("08/17/2015", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | SSN: ", None), ("078-45-9921", "SSN", "[SSN_1]"),
            ("\nVisitt Date: ", None), ("10/04/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nAttnding Allergst: ", None), ("Dr. Kimberly Mc'Ginnis, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nResidnce: ", None), ("742 Evergreen Terrace", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Springfield", "GEO_CITY", "[CITY_1]"),
            (", OR ", None), ("97477", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nCLINICAL HISTRY:\nJonny was evaluated for peanut anaphylaxis. Skin prick testing positive for Arachis hypogaea. Prescribed EpiPen Auto-Injector 0.15mg.\nEmergency Action Plan provided to Mother ", None),
            ("Rachel Braverman", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("541-555-0172", "PHONE", "[PHONE_1]"),
            (").\nReview in clinic on ", None),
            ("11/15/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nSigned: ", None),
            ("Kimberly Mc'Ginnis, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 5: GERIATRICS & PALLIATIVE CARE (6 Notes)
    # =========================================================================
    
    # Note 24: Age > 89 (94-year-old), Nonagenarian, DOB, Multi-date shifting
    notes.append(create_note(
        "SYNTH_NOTE_024",
        "Geriatrics & Palliative Care",
        "Geriatric Inpatient Comprehensive Assessment",
        ["age_over_89_geriatrics", "relative_timeline_preservation", "signatures_headers_footers"],
        [
            ("GERIATRIC COMPREHENSIVE INPATIENT ADMISSION NOTE\n", None),
            ("PATIENT: ", None), ("Florence Nightingale-Smith", "NAME_PATIENT", "[PATIENT_1]"),
            (" | AGE: ", None), ("94-year-old", "AGE_OVER_89", "[AGE_90+]"),
            (" | DOB: ", None), ("03/12/1929", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("GER-994820", "MRN", "[MRN_1]"),
            (" | ADMISSION DATE: ", None), ("10/12/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING GERIATRICIAN: ", None), ("Dr. Walter Cunningham, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1492019482", "LICENSE_NPI", "[NPI_1]"),
            (")\nFACILITY: ", None), ("Oakwood Senior Living & Subacute Care", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Evanston", "GEO_CITY", "[CITY_1]"),
            (", ", None), ("Cook County", "GEO_COUNTY", "[COUNTY_1]"),
            (", IL ", None), ("60201", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nHISTORY OF PRESENT ILLNESS:\nThe patient is a 94-year-old female admitted for delirium and urinary tract infection. She celebrated her 90th birthday in 2019. Resides in memory care unit.\n", None),
            ("CHRONOLOGY:\nSymptom onset on ", None),
            ("10/10/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (2 days prior to admission). IV ceftriaxone initiated. Mental status clearing.\nDischarge to assisted living planned 5 days post-admission on ", None),
            ("10/17/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (".\n\nGUARDIAN / POWER OF ATTORNEY: Son ", None),
            ("George Smith", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Cell: ", None),
            ("847-555-0199", "PHONE", "[PHONE_1]"),
            (" | Email: ", None),
            ("george.smith@oakwoodfamily.net", "EMAIL", "[EMAIL_1]"),
            (")\n\nAttending Signature: ", None),
            ("Walter Cunningham, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 25: Age > 89 (Centenarian, age 102), Palliative Care Transition, DEA
    notes.append(create_note(
        "SYNTH_NOTE_025",
        "Geriatrics & Palliative Care",
        "Palliative Care & Hospice Consultation Note",
        ["age_over_89_geriatrics", "signatures_headers_footers"],
        [
            ("PALLIATIVE MEDICINE & HOSPICE CONSULTATION\n", None),
            ("PATIENT: ", None), ("Arthur 'Grandpa Art' Pendelton", "NAME_PATIENT", "[PATIENT_1]"),
            (" | AGE: ", None), ("102 years old", "AGE_OVER_89", "[AGE_90+]"),
            (" (Centenarian) | DOB: ", None), ("01/15/1921", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("PAL-001928", "MRN", "[MRN_1]"),
            (" | CONSULT DATE: ", None), ("09/04/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nPALLIATIVE PHYSICIAN: ", None), ("Dr. Sarah Saunders, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (DEA: ", None), ("BS9948201", "LICENSE_DEA", "[LICENSE_1]"),
            (")\nFACILITY: ", None), ("St. Jude Palliative Hospice Pavilion", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Seattle", "GEO_CITY", "[CITY_1]"),
            (", WA ", None), ("98104", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nGOALS OF CARE:\nMr. Pendelton is a 102-year-old centenarian with end-stage congestive heart failure. Goals of care conference held with daughter ", None),
            ("Dorothy Pendelton-Adams", "NAME_FAMILY", "[FAMILY_1]"),
            (" and granddaughter ", None),
            ("Claire Adams", "NAME_FAMILY", "[FAMILY_2]"),
            (". Decision made to transition to comfort-focused hospice care.\nMedication order: Sublingual morphine for dyspnea.\nHospice coordinator contact: ", None),
            ("206-555-0147", "PHONE", "[PHONE_1]"),
            (" | Fax: ", None),
            ("206-555-0148", "FAX", "[FAX_1]"),
            ("\nSigned: ", None),
            ("Sarah Saunders, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 26: Age > 89 (91 yo nonagenarian), Fall & Hip Fracture, Table format
    notes.append(create_note(
        "SYNTH_NOTE_026",
        "Geriatrics & Palliative Care",
        "Geriatric Trauma & Orthopedic Co-Management",
        ["age_over_89_geriatrics", "tables_and_flowsheets", "relative_timeline_preservation"],
        [
            ("GERIATRIC TRAUMA CO-MANAGEMENT NOTE\n", None),
            ("PATIENT: ", None), ("Evelyn Dubois", "NAME_PATIENT", "[PATIENT_1]"),
            (" | AGE: ", None), ("91 yo", "AGE_OVER_89", "[AGE_90+]"),
            (" nonagenarian | DOB: ", None), ("08/14/1932", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("TRAUMA-9948", "MRN", "[MRN_1]"),
            (" | ADMIT DATE: ", None), ("11/15/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nCO-MANAGEMENT ATTENDING: ", None), ("Dr. Marcus Thorne, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | ORTHOPEDIC SURGEON: ", None), ("Dr. Alan Whipple-Scott, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\n\nCLINICAL FLOWSHEET:\n", None),
            ("| DATE | EVENT | CLINICAL STATUS |\n", None),
            ("| 11/15/2023 | Mechanical fall at home | Right femoral neck fracture confirmed |\n", None),
            ("| 11/16/2023 | Right Hemiarthroplasty | Performed by ", None),
            ("Dr. Whipple-Scott", "NAME_PROVIDER", "[PROVIDER_2]"),
            (" (Implant Lot: ", None),
            ("LOT-FEM-9948", "DEVICE", "[DEVICE_1]"),
            (") |\n| 11/17/2023 | Post-Op Day 1 | Patient Evelyn Dubois ambulating with walker |\n| 11/19/2023 | Post-Op Day 3 | Cleared for SNF transfer |\n\n", None),
            ("TRANSFER FACILITY: ", None),
            ("Silver Oaks Rehabilitation Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("500 Elm Street", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Skokie", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60077", "GEO_ZIP", "[ZIP_1]"),
            ("\nPhysician Signature: ", None),
            ("Marcus Thorne, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 27: Age > 89 (97-year-old), Memory care, Retinal scan ID, Medicare
    notes.append(create_note(
        "SYNTH_NOTE_027",
        "Geriatrics & Palliative Care",
        "Geriatric Ophthalmology & Memory Care Consult",
        ["age_over_89_geriatrics", "unusual_identifiers_telehealth"],
        [
            ("GERIATRIC OPHTHALMOLOGY CONSULTATION\n", None),
            ("PATIENT: ", None), ("Chester 'Chet' W. Robertson", "NAME_PATIENT", "[PATIENT_1]"),
            (" | AGE: ", None), ("97-year-old", "AGE_OVER_89", "[AGE_90+]"),
            (" | DOB: ", None), ("02/28/1926", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("OPH-00948", "MRN", "[MRN_1]"),
            (" | MEDICARE MBI: ", None), ("2JH5-MK8-PL99", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nDATE OF EXAM: ", None), ("06/20/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nOPHTHALMOLOGIST: ", None), ("Dr. Julian Horner-King, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nRETINAL SCAN BIOMETRIC ID: ", None),
            ("RET-SCAN-9948201", "BIOMETRIC", "[BIOMETRIC_1]"),
            ("\nFACILITY: ", None), ("Johns Hopkins Wilmer Eye Institute", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Baltimore", "GEO_CITY", "[CITY_1]"),
            (", MD ", None), ("21287", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nASSESSMENT:\nMr. Robertson is a 97-year-old with wet age-related macular degeneration. Intravitreal aflibercept injection administered.\nContact caregiver: Daughter ", None),
            ("Judith Robertson", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Cell: ", None),
            ("410-555-0165", "PHONE", "[PHONE_1]"),
            (").\nProvider Signature: ", None),
            ("Julian Horner-King, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 28: Age > 89 (89 borderline vs 90 yo), Nonagenarian transition
    notes.append(create_note(
        "SYNTH_NOTE_028",
        "Geriatrics & Palliative Care",
        "Geriatric Annual Wellness Visit",
        ["age_over_89_geriatrics", "mixed_formatting_and_delimiters"],
        [
            ("ANNUAL MEDICARE WELLNESS VISIT - GERIATRIC MEDICINE\n", None),
            ("PATIENT: ", None), ("Bernice Gable", "NAME_PATIENT", "[PATIENT_1]"),
            (" | CURRENT AGE: ", None), ("90 years old", "AGE_OVER_89", "[AGE_90+]"),
            (" (turned 90 on ", None), ("09/10/2023", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (") | DOB: ", None), ("09/10/1933", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("WELL-88301", "MRN", "[MRN_1]"),
            (" | ENCOUNTER DATE: ", None), ("09/15/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            ("\nPRIMARY PHYSICIAN: ", None), ("Dr. Alice Hamilton, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nRESIDENCE: ", None), ("884 Sunrise Senior Living Blvd, Apt 104", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Scottsdale", "GEO_CITY", "[CITY_1]"),
            (", ", None), ("Maricopa County", "GEO_COUNTY", "[COUNTY_1]"),
            (", AZ ", None), ("85251", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nNOTE:\nBernice was evaluated at age 89 last year and has now entered the nonagenarian age category upon turning 90 years old. Cognitive screening (Mini-Cog) 4/5. Fall risk assessment completed.\nFollow up in 1 year on ", None),
            ("09/15/2024", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (".\nContact phone: ", None),
            ("480-555-0182", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Alice Hamilton, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 29: Hospice Discharge / Mortality, Digital Signature, Account #
    notes.append(create_note(
        "SYNTH_NOTE_029",
        "Geriatrics & Palliative Care",
        "Hospice Inpatient Death & Discharge Summary",
        ["age_over_89_geriatrics", "signatures_headers_footers"],
        [
            ("HOSPICE INPATIENT DEATH & DISCHARGE SUMMARY\n", None),
            ("PATIENT: ", None), ("Donald 'Don' MacIntyre", "NAME_PATIENT", "[PATIENT_1]"),
            (" | AGE: ", None), ("95-year-old", "AGE_OVER_89", "[AGE_90+]"),
            (" | DOB: ", None), ("04/05/1928", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("HOSP-77402", "MRN", "[MRN_1]"),
            (" | HAR: ", None), ("HAR-88492014", "ACCOUNT", "[ACCOUNT_1]"),
            ("\nDATE OF DEATH: ", None), ("10/24/2023 03:45 EST", "DATE", "[DATE_2]", None),
            ("\nPRONOUNCING ATTENDING: ", None), ("Dr. Catherine O'Malley, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1584920193", "LICENSE_NPI", "[NPI_1]"),
            (")\nFACILITY: ", None), ("Mercy Hospice Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Pittsburgh", "GEO_CITY", "[CITY_1]"),
            (", PA ", None), ("15213", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nSUMMARY:\nMr. MacIntyre passed away peacefully in the presence of his daughter ", None),
            ("Helen MacIntyre-Reed", "NAME_FAMILY", "[FAMILY_1]"),
            (". Death due to cardiopulmonary arrest secondary to end-stage dementia.\nMortuary contact: ", None),
            ("412-555-0191", "PHONE", "[PHONE_1]"),
            ("\nElectronically Certified: ", None),
            ("Catherine O'Malley, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 6: PSYCHIATRY & BEHAVIORAL HEALTH (5 Notes)
    # =========================================================================
    
    # Note 30: Inpatient Intake, Legal Hold, Police Report #, SSN, Nicknames
    notes.append(create_note(
        "SYNTH_NOTE_030",
        "Psychiatry & Behavioral Health",
        "Psychiatric Inpatient Emergency Intake & Legal Hold",
        ["nicknames_and_aliases", "unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("EMERGENCY PSYCHIATRIC INTAKE & INVOLUNTARY HOLD (5150/BAKER ACT)\n", None),
            ("PATIENT: ", None), ("Gregory 'Greg' Houseman", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("07/19/1988", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | SSN: ", None), ("349-20-8841", "SSN", "[SSN_1]"),
            ("\nMRN: ", None), ("PSYCH-99482", "MRN", "[MRN_1]"),
            (" | POLICE REPORT #: ", None), ("CPD-2023-88491", "ID_ACCESSION", "[ID_1]"),
            ("\nDATE OF INTAKE: ", None), ("10/31/2023 23:15", "DATE", "[DATE_2]", None),
            ("\nEVALUATING PSYCHIATRIST: ", None), ("Dr. Carl Jung-Stevens, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | CRISIS WORKER: ", None), ("Sandra Bullock, LCSW", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nFACILITY: ", None), ("Cook County Health Behavioral Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Chicago", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60612", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nLEGAL BASIS & CLINICAL PRESENTATION:\nPatient brought by Chicago Police Department under involuntary 72-hour hold. Patient Greg Houseman exhibited paranoid delusions and auditory hallucinations. Denies suicidal ideation but placed on 1:1 safety observation.\nEmergency contact: Mother ", None),
            ("Barbara Houseman", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("312-555-0174", "PHONE", "[PHONE_1]"),
            (").\nCourt hearing scheduled for ", None),
            ("11/03/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (72 hours post-admission).\nSigned: ", None),
            ("Carl Jung-Stevens, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 31: Korsakoff syndrome & Wernicke's encephalopathy eponyms, Voiceprint ID
    notes.append(create_note(
        "SYNTH_NOTE_031",
        "Psychiatry & Behavioral Health",
        "Addiction Medicine & Neuropsychiatry Evaluation",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth"],
        [
            ("NEUROPSYCHIATRIC EVALUATION - ADDICTION MEDICINE\n", None),
            ("PATIENT: ", None), ("Timothy 'Tim' O'Reilly", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("11/14/1970", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ADDICT-8839", "MRN", "[MRN_1]"),
            ("\nEVALUATION DATE: ", None), ("08/29/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING PSYCHIATRIST: ", None), ("Dr. Sergei Korsakoff-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nVOICEPRINT BIOMETRIC ID: ", None),
            ("VP-BIO-99482014", "BIOMETRIC", "[BIOMETRIC_1]"),
            ("\nFACILITY: ", None), ("McLean Hospital Psychiatric Pavilion", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Belmont", "GEO_CITY", "[CITY_1]"),
            (", MA ", None), ("02478", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nFINDINGS:\nPatient evaluated for severe alcohol use disorder with anterograde amnesia and confabulation. Examined by Dr. Korsakoff-Miller. Diagnosis: Wernicke-Korsakoff syndrome (Wernicke's encephalopathy treated with high-dose IV thiamine, residual Korsakoff syndrome).\nDischarge to residential rehab on ", None),
            ("09/12/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (14 days post-eval).\nContact caseworker: ", None),
            ("617-555-0155", "PHONE", "[PHONE_1]"),
            ("\nSignature: ", None),
            ("Sergei Korsakoff-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 32: Outpatient Psychotherapy, Telehealth URL, License Plate, Email
    notes.append(create_note(
        "SYNTH_NOTE_032",
        "Psychiatry & Behavioral Health",
        "Outpatient Psychotherapy Session Note",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("OUTPATIENT PSYCHOTHERAPY PROGRESS NOTE\n", None),
            ("PATIENT: ", None), ("Melissa 'Missy' Armstrong", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("03/27/1995", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("THER-44910", "MRN", "[MRN_1]"),
            ("\nSESSION DATE: ", None), ("09/18/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nCLINICAL PSYCHOLOGIST: ", None), ("Dr. Sigmund Freud-Harris, PsyD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (License: ", None), ("PSY-CA-99482", "LICENSE_STATE", "[LICENSE_1]"),
            (")\nTELEHEALTH URL: ", None),
            ("https://therapyportal.com/session/missy_armstrong_99", "URL", "[URL_1]"),
            ("\nPATIENT VEHICLE TAG: ", None), ("CA 8ABC123", "VEHICLE", "[VEHICLE_1]"),
            ("\n\nSESSION SUMMARY:\nMissy attended 50-minute cognitive behavioral therapy (CBT) session for Generalized Anxiety Disorder. Discussed exposure hierarchy.\nNext session scheduled on ", None),
            ("09/25/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nPatient email: ", None),
            ("missy.armstrong95@yahoo.com", "EMAIL", "[EMAIL_1]"),
            (" | Clinic Phone: ", None),
            ("415-555-0138", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Sigmund Freud-Harris, PsyD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 33: Pediatric Psychiatry, Parent guardian, ADHD, Insurance group #
    notes.append(create_note(
        "SYNTH_NOTE_033",
        "Psychiatry & Behavioral Health",
        "Child & Adolescent Psychiatry Diagnostic Intake",
        ["nicknames_and_aliases", "mixed_formatting_and_delimiters"],
        [
            ("CHILD & ADOLESCENT PSYCHIATRY INTAKE\n", None),
            ("PATIENT: ", None), ("Lucas 'Luke' Donahue", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("08/12/2012", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("CAP-88301", "MRN", "[MRN_1]"),
            (" | INS POLICY #: ", None), ("AETNA-994820", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            (" | GRP: ", None), ("GRP-77402", "HEALTHPLAN", "[HEALTHPLAN_2]"),
            ("\nVISIT DATE: ", None), ("10/11/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nCHILD PSYCHIATRIST: ", None), ("Dr. Karen Horney-White, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nLEGAL GUARDIANS: Mother ", None),
            ("Claire Donahue", "NAME_FAMILY", "[FAMILY_1]"),
            (" and Stepfather ", None),
            ("Peter Donahue", "NAME_FAMILY", "[FAMILY_2]"),
            ("\nADDRESS: ", None), ("312 Maple Leaf Way", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Seattle", "GEO_CITY", "[CITY_1]"),
            (", WA ", None), ("98105", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nEVALUATION:\nLuke is an 11-year-old male evaluated for ADHD, combined type, and school refusal. Initiating methylphenidate ER 18mg.\nFollow-up medication check in 4 weeks on ", None),
            ("11/08/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact: ", None),
            ("206-555-0164", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Karen Horney-White, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 34: Geriatric Psychiatry, Alzheimer's vs Dr. Alzheimer, Nonagenarian
    notes.append(create_note(
        "SYNTH_NOTE_034",
        "Psychiatry & Behavioral Health",
        "Geriatric Psychiatry Inpatient Consultation",
        ["age_over_89_geriatrics", "eponym_vs_doctor_name"],
        [
            ("GERIATRIC PSYCHIATRY INPATIENT NOTE\n", None),
            ("PATIENT: ", None), ("Mildred 'Millie' Van Der Bilt", "NAME_PATIENT", "[PATIENT_1]"),
            (" | AGE: ", None), ("92 years old", "AGE_OVER_89", "[AGE_90+]"),
            (" | DOB: ", None), ("05/04/1931", "DATE", "[DATE_1]", "%m/%d/%Y"),
            ("\nMRN: ", None), ("GERPSY-0091", "MRN", "[MRN_1]"),
            (" | DATE: ", None), ("09/14/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nPSYCHIATRIST: ", None), ("Dr. Emil Kraepelin-Jones, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nNURSING HOME: ", None), ("St. Joseph Senior Care Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Philadelphia", "GEO_CITY", "[CITY_1]"),
            (", PA ", None), ("19104", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nIMPRESSION: 92-year-old female with advanced Alzheimer's dementia presenting with sundowning and agitation. Dr. Kraepelin-Jones recommended low-dose melatonin and environmental modifications.\nFollow-up in 2 weeks on ", None),
            ("09/28/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nFamily Contact: Son ", None),
            ("Arthur Van Der Bilt", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("215-555-0187", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("Emil Kraepelin-Jones, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 7: ORTHOPEDICS & SPORTS MEDICINE (5 Notes)
    # =========================================================================
    
    # Note 35: Total Knee Arthroplasty Operative Note, Implant UDI & SN, Relative timeline
    notes.append(create_note(
        "SYNTH_NOTE_035",
        "Orthopedics & Sports Medicine",
        "Total Knee Arthroplasty Operative Report",
        ["unusual_identifiers_telehealth", "relative_timeline_preservation", "signatures_headers_footers"],
        [
            ("DEPARTMENT OF ORTHOPEDIC SURGERY OPERATIVE RECORD\n", None),
            ("PATIENT: ", None), ("Richard 'Dick' Grayson", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("06/18/1959", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ORTHO-9948", "MRN", "[MRN_1]"),
            ("\nSURGERY DATE: ", None), ("07/10/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING ORTHOPEDIC SURGEON: ", None), ("Dr. Robert Tinel-Adams, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1774920194", "LICENSE_NPI", "[NPI_1]"),
            (")\nFACILITY: ", None), ("Hospital for Special Surgery", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("535 E 70th St", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("New York", "GEO_CITY", "[CITY_1]"),
            (", NY ", None), ("10021", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPROCEDURE: Right Total Knee Arthroplasty (TKA).\n", None),
            ("IMPLANT LOG:\nFemoral Component SN: ", None),
            ("SN-TKA-FEM-8849", "DEVICE", "[DEVICE_1]"),
            (" | Tibial Tray SN: ", None),
            ("SN-TKA-TIB-8850", "DEVICE", "[DEVICE_2]"),
            ("\nPolyethylene Insert Lot: ", None),
            ("LOT-POLY-2023-99", "DEVICE", "[DEVICE_3]"),
            ("\nUDI: ", None),
            ("(01)00884920148291(17)280710(10)LOT99", "DEVICE", "[DEVICE_4]"),
            ("\n\nPOST-OP TIMELINE: Physical therapy initiated on post-op day 1 (07/11/2023). Knee flexion reached 95 degrees by post-op day 3 (07/13/2023). Discharge home on ", None),
            ("07/13/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact Ortho clinic: ", None),
            ("212-555-0182", "PHONE", "[PHONE_1]"),
            ("\nDictated by: ", None),
            ("Robert Tinel-Adams, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 36: Carpal Tunnel Release, Phalen's maneuver & Tinel's sign eponyms
    notes.append(create_note(
        "SYNTH_NOTE_036",
        "Orthopedics & Sports Medicine",
        "Hand Surgery Outpatient Clinic Note",
        ["eponym_vs_doctor_name", "signatures_headers_footers"],
        [
            ("OUTPATIENT HAND SURGERY CONSULTATION\n", None),
            ("PATIENT: ", None), ("Beverly Crusher-Smith", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("09/21/1968", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("HAND-0092", "MRN", "[MRN_1]"),
            ("\nVISIT DATE: ", None), ("10/16/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nHAND SURGEON: ", None), ("Dr. Jules Tinel, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | FELLOW: ", None), ("Dr. George Phalen-Miller, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nCLINIC: ", None), ("Midwest Orthopedic Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Chicago", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60614", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPHYSICAL EXAMINATION:\nRight hand examination reveals positive Tinel's sign over median nerve at wrist and positive Phalen's maneuver within 30 seconds. Exam verified by ", None),
            ("Dr. Tinel", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" and ", None),
            ("Dr. Phalen-Miller", "NAME_PROVIDER", "[PROVIDER_2]"),
            (".\nIMPRESSION: Severe right carpal tunnel syndrome.\nPLAN: Right endoscopic carpal tunnel release scheduled for ", None),
            ("11/06/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nEmergency Contact: Spouse ", None),
            ("Jack Crusher", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("312-555-0179", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("Jules Tinel, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 37: ACL Reconstruction Operative Record, Lachman & McMurray signs, Table
    notes.append(create_note(
        "SYNTH_NOTE_037",
        "Orthopedics & Sports Medicine",
        "Sports Medicine ACL Reconstruction Operative Note",
        ["eponym_vs_doctor_name", "tables_and_flowsheets", "signatures_headers_footers"],
        [
            ("SPORTS MEDICINE SURGICAL OPERATIVE RECORD\n", None),
            ("PATIENT: ", None), ("Lucas 'Luke' Cage", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("02/14/1998", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("SPORTS-883", "MRN", "[MRN_1]"),
            ("\nDATE OF SURGERY: ", None), ("08/22/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nSURGEON: ", None), ("Dr. John Lachman-Scott, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1664920194", "LICENSE_NPI", "[NPI_1]"),
            (")\nASSISTANT: ", None), ("Dr. Thomas McMurray, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\n\nPRE-OP EXAM:\nPositive Lachman test with soft endpoint; positive McMurray test on medial joint line. Dr. Lachman-Scott and Dr. McMurray confirmed complete ACL tear.\n\n", None),
            ("OPERATIVE DETAILS TABLE:\n", None),
            ("| COMPONENT | SPECIFICATION | LOT / SERIAL |\n", None),
            ("| Graft | Bone-patellar tendon-bone autograft | Autologous |\n", None),
            ("| Femoral Fixation | Interference Screw 7x25mm | ", None),
            ("LOT-SCREW-99482", "DEVICE", "[DEVICE_1]"),
            (" |\n| Tibial Fixation | BioComposite Screw 9x30mm | ", None),
            ("LOT-SCREW-99483", "DEVICE", "[DEVICE_2]"),
            (" |\n\nREHABILITATION: Hinged knee brace locked in extension. PT begins on ", None),
            ("08/25/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (3 days post-op).\nSigned: ", None),
            ("John Lachman-Scott, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 38: Pediatric Orthopedics, Clubfoot / Ponseti method vs Dr. Ponseti
    notes.append(create_note(
        "SYNTH_NOTE_038",
        "Orthopedics & Sports Medicine",
        "Pediatric Orthopedic Clubfoot Management Note",
        ["eponym_vs_doctor_name", "nicknames_and_aliases"],
        [
            ("PEDIATRIC ORTHOPEDIC CLINIC NOTE\n", None),
            ("PATIENT: ", None), ("Oliver 'Ollie' Queen-Smith", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("06/01/2023", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("PED-ORTHO-019", "MRN", "[MRN_1]"),
            ("\nVISIT DATE: ", None), ("07/15/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            (" (6 weeks of life)\n", None),
            ("PEDIATRIC ORTHOPEDIST: ", None), ("Dr. Ignacio Ponseti-Taylor, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nPARENTS: Mother ", None),
            ("Dinah Queen", "NAME_FAMILY", "[FAMILY_1]"),
            (" and Father ", None),
            ("Oliver Queen Sr.", "NAME_FAMILY", "[FAMILY_2]"),
            ("\nCLINIC: ", None), ("Children's Hospital of Philadelphia", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Philadelphia", "GEO_CITY", "[CITY_1]"),
            (", PA ", None), ("19104", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nMANAGEMENT:\nInfant evaluated for congenital talipes equinovarus (bilateral clubfoot). Dr. Ponseti-Taylor applied serial casting using the standard Ponseti method. Cast #4 applied today.\nPercutaneous Achilles tenotomy planned for ", None),
            ("08/12/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact phone: ", None),
            ("215-555-0144", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Ignacio Ponseti-Taylor, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 39: Spine Deformity, Trendelenburg sign & position, Digital signature
    notes.append(create_note(
        "SYNTH_NOTE_039",
        "Orthopedics & Sports Medicine",
        "Spine & Scoliosis Clinical Evaluation",
        ["eponym_vs_doctor_name", "signatures_headers_footers"],
        [
            ("SPINE & SCOLIOSIS CENTER CONSULTATION\n", None),
            ("PATIENT: ", None), ("Cassandra 'Cassie' Lang", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("10/30/2007", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("SCOL-8849", "MRN", "[MRN_1]"),
            ("\nDATE OF VISIT: ", None), ("09/05/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nSPINE SURGEON: ", None), ("Dr. Friedrich Trendelenburg-Brown, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (DEA: ", None), ("BT8849201", "LICENSE_DEA", "[LICENSE_1]"),
            (")\nHOME ADDRESS: ", None), ("1042 Elmwood Ave, Apt 4B", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("Oak Park", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60301", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPHYSICAL FINDINGS:\nPatient evaluated for adolescent idiopathic scoliosis (Cobb angle 34 degrees). Gait analysis shows negative Trendelenburg sign bilaterally. During examination, patient placed in Trendelenburg position for pelvic alignment.\nDr. Trendelenburg-Brown recommended custom thoracic-lumbar-sacral orthosis (TLSO brace).\nFollow-up with repeat EOS X-rays on ", None),
            ("03/05/2024", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nEmergency Contact: Father ", None),
            ("Scott Lang", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Cell: ", None),
            ("312-555-0158", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("Friedrich Trendelenburg-Brown, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 8: GASTROENTEROLOGY & HEPATOLOGY (5 Notes)
    # =========================================================================
    
    # Note 40: Crohn's disease vs Dr. Crohn, Barrett's esophagus, Colonoscopy
    notes.append(create_note(
        "SYNTH_NOTE_040",
        "Gastroenterology & Hepatology",
        "Gastroenterology Colonoscopy & Endoscopy Report",
        ["eponym_vs_doctor_name", "signatures_headers_footers", "relative_timeline_preservation"],
        [
            ("DIGESTIVE DISEASE CENTER ENDOSCOPY REPORT\n", None),
            ("PATIENT: ", None), ("Jonathan 'Jon'athan Harker", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("04/18/1980", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("GI-994820", "MRN", "[MRN_1]"),
            ("\nPROCEDURE DATE: ", None), ("08/17/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nENDOSCOPIST: ", None), ("Dr. Burrill B. Crohn-Smith, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | ATTENDING: ", None), ("Dr. Norman Barrett-Lee, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nFACILITY: ", None), ("Mount Sinai Hospital Endoscopy Suite", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("New York", "GEO_CITY", "[CITY_1]"),
            (", NY ", None), ("10029", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nFINDINGS:\n1. EGD: Short-segment Barrett's esophagus (Prague C1M2) confirmed; biopsies obtained. Dr. Barrett-Lee reviewed esophageal mucosal pattern.\n2. Colonoscopy: Active ileitis with mucosal ulcerations and cobblestoning consistent with moderate Crohn's disease. Dr. Crohn-Smith evaluated terminal ileum.\n\n", None),
            ("PATHOLOGY & TIMELINE:\nBiopsy specimens sent under Accession #: ", None),
            ("PATH-GI-2023-9948", "ID_ACCESSION", "[ID_1]"),
            (".\nFollow-up in clinic in 2 weeks on ", None),
            ("08/31/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" to discuss biologic therapy with infliximab.\nCallback: ", None),
            ("212-555-0163", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Burrill B. Crohn-Smith, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 41: Zollinger-Ellison syndrome, Mallory-Weiss tear, Table
    notes.append(create_note(
        "SYNTH_NOTE_041",
        "Gastroenterology & Hepatology",
        "Gastroenterology Inpatient Consult",
        ["eponym_vs_doctor_name", "tables_and_flowsheets"],
        [
            ("INPATIENT GASTROENTEROLOGY CONSULTATION NOTE\n", None),
            ("PATIENT: ", None), ("Diana Prince-Trevor", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("11/25/1975", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("GI-INP-004", "MRN", "[MRN_1]"),
            ("\nDATE OF CONSULT: ", None), ("10/02/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nCONSULTANT: ", None), ("Dr. Robert Zollinger-Vance, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | FELLOW: ", None), ("Dr. George Mallory-Adams, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nHOSPITAL: ", None), ("Cedars-Sinai Medical Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Los Angeles", "GEO_CITY", "[CITY_1]"),
            (", CA ", None), ("90048", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nLABORATORY LOG:\n", None),
            ("| TEST | RESULT | REFERENCE RANGE |\n", None),
            ("| Serum Gastrin | 1450 pg/mL | < 100 pg/mL |\n", None),
            ("| Gastric pH | 1.4 | 1.5 - 3.5 |\n", None),
            ("| Hemoglobin | 9.8 g/dL | 12.0 - 15.5 g/dL |\n\n", None),
            ("CLINICAL SYNTHESIS:\nPatient with recurrent peptic ulcer disease and marked hypergastrinemia, highly suspicious for Zollinger-Ellison syndrome (gastrinoma). Upper endoscopy also demonstrated healing Mallory-Weiss tear at gastroesophageal junction. Evaluated by Dr. Zollinger-Vance and Dr. Mallory-Adams.\n\n", None),
            ("PLAN:\n1. Secretin stimulation test on ", None),
            ("10/05/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (3 days post-consult).\n2. Somatostatin receptor scintigraphy.\nSigned: ", None),
            ("Robert Zollinger-Vance, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 42: Whipple's disease & Hashimoto's thyroiditis, IP address, Telehealth
    notes.append(create_note(
        "SYNTH_NOTE_042",
        "Gastroenterology & Hepatology",
        "Hepatology & Malabsorption Telehealth Note",
        ["eponym_vs_doctor_name", "unusual_identifiers_telehealth"],
        [
            ("TELEHEALTH GASTROENTEROLOGY CONSULTATION\n", None),
            ("PATIENT: ", None), ("Arthur 'Artie' Dent", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("03/11/1972", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("GI-TELE-88", "MRN", "[MRN_1]"),
            ("\nCONSULT DATE: ", None), ("09/08/2023 14:00 CST", "DATE", "[DATE_2]", None),
            ("\nGASTROENTEROLOGIST: ", None), ("Dr. George Whipple-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nPORTAL ZOOM URL: ", None),
            ("https://telemed.uchicago.edu/room/artie_dent_9948", "URL", "[URL_1]"),
            ("\nREMOTE IP: ", None),
            ("172.16.42.108", "IP", "[IP_1]"),
            ("\n\nNOTE:\nFollow-up for chronic diarrhea, arthralgias, and weight loss. Duodenal biopsy confirmed PAS-positive macrophages diagnostic of Whipple's disease (Tropheryma whipplei infection). Concomitant Hashimoto's thyroiditis treated with levothyroxine.\nDr. Whipple-Miller prescribed long-term trimethoprim-sulfamethoxazole.\nRepeat PCR in 6 months on ", None),
            ("03/08/2024", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact email: ", None),
            ("artie.dent72@gmail.com", "EMAIL", "[EMAIL_1]"),
            ("\nSigned: ", None),
            ("George Whipple-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 43: Liver Transplant Clinic, Biometric voice, Insurance MBI, Phone
    notes.append(create_note(
        "SYNTH_NOTE_043",
        "Gastroenterology & Hepatology",
        "Transplant Hepatology Post-Op Evaluation",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("TRANSPLANT HEPATOLOGY CLINIC NOTE\n", None),
            ("PATIENT: ", None), ("Bruce W. Wayne-Campbell", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("05/27/1967", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("TX-LIV-0091", "MRN", "[MRN_1]"),
            (" | MBI: ", None), ("3MK8-PL9-TT44", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nVISIT DATE: ", None), ("08/01/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nTRANSPLANT HEPATOLOGIST: ", None), ("Dr. Melissa Vance-Sterling, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1994820193", "LICENSE_NPI", "[NPI_1]"),
            (")\nVOICE BIOMETRIC ID: ", None),
            ("VOICE-BIO-884920", "BIOMETRIC", "[BIOMETRIC_1]"),
            ("\nFACILITY: ", None), ("UPMC Center for Liver Diseases", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Pittsburgh", "GEO_CITY", "[CITY_1]"),
            (", PA ", None), ("15213", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nASSESSMENT: Orthotopic liver transplantation performed on ", None),
            ("05/01/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (3 months post-transplant). Tacrolimus trough level 7.2 ng/mL (target 6-8). LFTs completely normalized.\nNext clinic visit on ", None),
            ("09/01/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (".\nTransplant Coordinator: ", None),
            ("412-555-0139", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Melissa Vance-Sterling, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 44: Endoscopic Retrograde Cholangiopancreatography (ERCP), Stent SN, Table
    notes.append(create_note(
        "SYNTH_NOTE_044",
        "Gastroenterology & Hepatology",
        "Therapeutic ERCP Operative Record",
        ["tables_and_flowsheets", "unusual_identifiers_telehealth"],
        [
            ("INTERVENTIONAL ENDOSCOPY OPERATIVE REPORT (ERCP)\n", None),
            ("PATIENT: ", None), ("Victor 'Vic' Stone", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("01/10/1985", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ERCP-88401", "MRN", "[MRN_1]"),
            ("\nPROCEDURE DATE: ", None), ("07/25/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nINTERVENTIONAL ENDOSCOPIST: ", None), ("Dr. Alexander Murphy-Lee, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nHOSPITAL: ", None), ("Mayo Clinic Hospital - Rochester", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Rochester", "GEO_CITY", "[CITY_1]"),
            (", ", None), ("Olmsted County", "GEO_COUNTY", "[COUNTY_1]"),
            (", MN ", None), ("55902", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nIMPLANTED DEVICE TABLE:\n", None),
            ("| STENT TYPE | DIAMETER / LENGTH | SERIAL / LOT NUMBER |\n", None),
            ("| Biliary Fully Covered Metal Stent | 10mm x 60mm | ", None),
            ("SN-STENT-99482-B", "DEVICE", "[DEVICE_1]"),
            (" |\n| Pancreatic Duct Plastic Stent | 5 Fr x 4cm | ", None),
            ("LOT-PLAST-8849", "DEVICE", "[DEVICE_2]"),
            (" |\n\nNARRATIVE: Successful biliary sphincterotomy and stent placement for choledocholithiasis. Examined by Dr. Murphy-Lee. Post-procedure serum lipase monitoring.\nStent exchange scheduled in 3 months on ", None),
            ("10/25/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact: ", None),
            ("507-555-0188", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Alexander Murphy-Lee, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 9: TELEHEALTH & INFECTIOUS DISEASE (5 Notes)
    # =========================================================================
    
    # Note 45: Telemedicine Session Log, IPv6 & IPv4, Zoom URL, Relative dates
    notes.append(create_note(
        "SYNTH_NOTE_045",
        "Telehealth & Infectious Disease",
        "Telemedicine Infectious Disease Consultation Log",
        ["unusual_identifiers_telehealth", "relative_timeline_preservation", "signatures_headers_footers"],
        [
            ("TELEHEALTH CLINICAL ENCOUNTER LOG & ENCRYPTED TRANSMISSION RECORD\n", None),
            ("PATIENT: ", None), ("Natasha 'Nat' Romanoff", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("12/03/1984", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ID-TELE-9948", "MRN", "[MRN_1]"),
            ("\nSESSION TIMESTAMP: ", None), ("10/08/2023 15:30 UTC", "DATE", "[DATE_2]", None),
            ("\nINFECTIOUS DISEASE SPECIALIST: ", None), ("Dr. Anthony Fauci-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1884920188", "LICENSE_NPI", "[NPI_1]"),
            (")\nSESSION URL: ", None),
            ("https://telehealth.nih.gov/secure/v_room_99482014", "URL", "[URL_1]"),
            ("\nCLIENT IPv4: ", None),
            ("198.51.100.155", "IP", "[IP_1]"),
            (" | CLIENT IPv6: ", None),
            ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "IP", "[IP_2]"),
            ("\n\nCLINICAL TIMELINE & PROGRESS:\nPatient evaluated for persistent Lyme disease symptoms following tick bite on ", None),
            ("09/01/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (" (37 days prior). Erythema migrans rash documented. Completed 21-day course of doxycycline.\nDr. Fauci-Miller noted marked resolution of arthralgias.\nFollow-up virtual check-in in 4 weeks on ", None),
            ("11/05/2023", "DATE", "[DATE_4]", "%m/%d/%Y"),
            (".\nSecure portal: ", None),
            ("https://patient.idclinic.nih.gov/portal/natasha_r", "URL", "[URL_2]"),
            (" | Callback: ", None),
            ("301-555-0144", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Anthony Fauci-Miller, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 46: COVID-19 & Paxlovid Telehealth, Retinal Scan ID, Pharmacy Address
    notes.append(create_note(
        "SYNTH_NOTE_046",
        "Telehealth & Infectious Disease",
        "Virtual Urgent Care Encounter Note",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("VIRTUAL URGENT CARE CLINICAL ASSESSMENT\n", None),
            ("PATIENT: ", None), ("Peter 'Spidey' Parker", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("08/10/2001", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("VUC-44910", "MRN", "[MRN_1]"),
            ("\nENCOUNTER DATE: ", None), ("11/05/2023 09:15 EST", "DATE", "[DATE_2]", None),
            ("\nURGENT CARE PHYSICIAN: ", None), ("Dr. Stephen Strange, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (License: ", None), ("NY-MD-098421", "LICENSE_STATE", "[LICENSE_1]"),
            (")\nTELEMEDICINE PLATFORM: ", None),
            ("https://urgentcare.nyulangone.org/room/pat_spidey88", "URL", "[URL_1]"),
            ("\nPATIENT IP: ", None),
            ("10.240.12.8", "IP", "[IP_1]"),
            ("\n\nNOTE:\nPatient with acute symptomatic COVID-19 (PCR positive 11/04/2023). Dr. Strange prescribed Paxlovid.\nPrescription e-sent to CVS Pharmacy: ", None),
            ("1450 Broadway Ave", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("New York", "GEO_CITY", "[CITY_1]"),
            (", NY ", None), ("10018", "GEO_ZIP", "[ZIP_1]"),
            (" (Pharmacy Phone: ", None),
            ("212-555-0198", "PHONE", "[PHONE_1]"),
            (").\nPatient email: ", None),
            ("peter.parker.daily@gmail.com", "EMAIL", "[EMAIL_1]"),
            ("\nSigned: ", None),
            ("Stephen Strange, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 47: HIV PrEP Management, Lab Accession ID, Medicaid ID, Table
    notes.append(create_note(
        "SYNTH_NOTE_047",
        "Telehealth & Infectious Disease",
        "Infectious Disease PrEP Management Note",
        ["tables_and_flowsheets", "unusual_identifiers_telehealth"],
        [
            ("INFECTIOUS DISEASE OUTPATIENT PrEP CLINIC NOTE\n", None),
            ("PATIENT: ", None), ("Wade 'Deadpool' Wilson", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("11/22/1983", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ID-PREP-88", "MRN", "[MRN_1]"),
            (" | MEDICAID ID: ", None), ("MCD-NY-9948201", "HEALTHPLAN", "[HEALTHPLAN_1]"),
            ("\nVISIT DATE: ", None), ("09/12/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nATTENDING PHYSICIAN: ", None), ("Dr. Wade Barrett-Chen, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\n\nQUARTERLY LAB SCREENING TABLE:\n", None),
            ("| TEST | RESULT | LAB ACCESSION # |\n", None),
            ("| HIV-1/2 Ag/Ab 4th Gen | Non-reactive | ", None),
            ("ACC-HIV-2023-884", "ID_ACCESSION", "[ID_1]"),
            (" |\n| Serum Creatinine | 0.92 mg/dL | ", None),
            ("ACC-CMP-2023-885", "ID_ACCESSION", "[ID_2]"),
            (" |\n| Hepatitis B sAg / sAb | Immune (sAb > 100) | ", None),
            ("ACC-HEP-2023-886", "ID_ACCESSION", "[ID_3]"),
            (" |\n\nPLAN: Continue emtricitabine/tenofovir disoproxil fumarate (Truvada) 200/300 mg daily. Reviewed by Dr. Barrett-Chen.\nNext quarterly labs due on ", None),
            ("12/12/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (".\nContact phone: ", None),
            ("212-555-0177", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Wade Barrett-Chen, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 48: Tuberculosis Contact Tracing, Public Health, Case ID, Fax
    notes.append(create_note(
        "SYNTH_NOTE_048",
        "Telehealth & Infectious Disease",
        "Public Health Tuberculosis Case Investigation",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("PUBLIC HEALTH DEPARTMENT TUBERCULOSIS INVESTIGATION\n", None),
            ("PATIENT: ", None), ("Gwen Stacy-Parker", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("07/15/1996", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | TB CASE ID: ", None), ("TB-CASE-2023-9948", "ID_ACCESSION", "[ID_1]"),
            ("\nDATE OF REPORT: ", None), ("10/19/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nINVESTIGATING EPIDEMIOLOGIST: ", None), ("Dr. Robert Koch-Taylor, MD, MPH", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nHEALTH DEPT: ", None), ("Cook County Department of Public Health", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Forest Park", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60130", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nCONTACT TRACING LOG:\nPatient identified as close contact of confirmed pulmonary TB index case. QuantiFERON-TB Gold Plus positive on ", None),
            ("10/15/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (". Chest X-ray clear without cavitary lesions (Latent TB Infection). Prescribed 3HP regimen (rifapentine + isoniazid weekly x 12 weeks).\nDirectly Observed Therapy (DOT) coordinator phone: ", None),
            ("708-555-0144", "PHONE", "[PHONE_1]"),
            (" | Confidential Fax: ", None),
            ("708-555-0145", "FAX", "[FAX_1]"),
            ("\nSigned: ", None),
            ("Robert Koch-Taylor, MD, MPH", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 49: Remote Patient Monitoring, Bluetooth Pulse Oximeter SN, Telehealth IP
    notes.append(create_note(
        "SYNTH_NOTE_049",
        "Telehealth & Infectious Disease",
        "Remote Patient Monitoring Telemetry Log",
        ["unusual_identifiers_telehealth", "tables_and_flowsheets"],
        [
            ("REMOTE PATIENT MONITORING (RPM) TELEMETRY REPORT\n", None),
            ("PATIENT: ", None), ("Matthew 'Matt' Murdock", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("09/11/1981", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("RPM-88402", "MRN", "[MRN_1]"),
            ("\nLOG PERIOD: ", None), ("11/01/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            (" to ", None), ("11/07/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            ("\nMONITORING NURSE: ", None), ("Claire Temple, RN", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nSUPERVISING PHYSICIAN: ", None), ("Dr. Stephen Strange, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nDEVICE: Masimo Bluetooth Pulse Oximeter SN: ", None),
            ("SN-MASIMO-99482", "DEVICE", "[DEVICE_1]"),
            ("\nGATEWAY HUB IP: ", None),
            ("192.0.2.148", "IP", "[IP_1]"),
            ("\n\nDAILY SPO2 TELEMETRY LOG:\n", None),
            ("| DATE | TIME | HEART RATE | SPO2 | TRANSMISSION STATUS |\n", None),
            ("| 11/01/2023 | 08:00 | 72 bpm | 98% | OK |\n", None),
            ("| 11/03/2023 | 08:00 | 74 bpm | 97% | OK |\n", None),
            ("| 11/05/2023 | 08:00 | 70 bpm | 99% | OK |\n| 11/07/2023 | 08:00 | 71 bpm | 98% | OK |\n\n", None),
            ("SUMMARY: Vital signs stable on home oxygen weaning. Reviewed by Nurse Claire Temple.\nRPM Clinical Hotline: ", None),
            ("212-555-0133", "PHONE", "[PHONE_1]"),
            ("\nSigned: ", None),
            ("Claire Temple, RN", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))

    # =========================================================================
    # SPECIALTY 10: EMERGENCY MEDICINE & TRAUMA RESUSCITATION (6 Notes)
    # =========================================================================
    
    # Note 50: Trauma Resuscitation Flowsheet, Glasgow Coma Scale, Rapid timestamps
    notes.append(create_note(
        "SYNTH_NOTE_050",
        "Emergency Medicine & Trauma",
        "Trauma Resuscitation Emergency Flowsheet",
        ["eponym_vs_doctor_name", "tables_and_flowsheets", "signatures_headers_footers"],
        [
            ("LEVEL 1 TRAUMA CENTER RESUSCITATION RECORD\n", None),
            ("PATIENT: ", None), ("Bruce 'Hulk' Banner", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("12/18/1969", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("TRAUMA-0091", "MRN", "[MRN_1]"),
            ("\nTRAUMA ACTIVATION TIME: ", None), ("10/25/2023 21:14", "DATE", "[DATE_2]", None),
            ("\nTRAUMA TEAM LEADER: ", None), ("Dr. William Halsted-Reed, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None), ("1449201948", "LICENSE_NPI", "[NPI_1]"),
            (")\nEMERGENCY MEDICINE ATTENDING: ", None), ("Dr. Christine Palmer, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nHOSPITAL: ", None), ("Cook County Stroger Trauma Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Chicago", "GEO_CITY", "[CITY_1]"),
            (", IL ", None), ("60612", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nTRAUMA FLOWSHEET:\n", None),
            ("| TIME | STEP | OPERATOR | DETAILS |\n", None),
            ("| 21:15 | Primary Survey | ", None), ("Dr. Palmer", "NAME_PROVIDER", "[PROVIDER_2]"),
            (" | Airway intact, Glasgow Coma Scale (GCS) 14 |\n", None),
            ("| 21:20 | FAST Ultrasound | ", None), ("Dr. Halsted-Reed", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | FAST exam negative in Morison's pouch and splenorenal recess |\n", None),
            ("| 21:35 | Pelvic X-Ray | ", None), ("Dr. Halsted-Reed", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | Stable pelvic ring, no open book fracture |\n\n", None),
            ("DISPOSITION: Admitted to Trauma ICU for 24-hour serial abdominal exams under Dr. Halsted-Reed.\nEmergency contact: Sister ", None),
            ("Jennifer Walters", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("312-555-0195", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("William Halsted-Reed, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 51: Acute Appendicitis, McBurney's point & Murphy's sign eponyms
    notes.append(create_note(
        "SYNTH_NOTE_051",
        "Emergency Medicine & Trauma",
        "Emergency Department Triage & Surgical Consult Note",
        ["eponym_vs_doctor_name", "relative_timeline_preservation"],
        [
            ("EMERGENCY DEPARTMENT CLINICAL ASSESSMENT\n", None),
            ("PATIENT: ", None), ("Clinton 'Clint' Barton", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("01/07/1971", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ED-88402", "MRN", "[MRN_1]"),
            ("\nTRIAGE TIME: ", None), ("09/18/2023 03:20 EST", "DATE", "[DATE_2]", None),
            ("\nED ATTENDING: ", None), ("Dr. Charles McBurney-Jones, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" | SURGICAL RESIDENT: ", None), ("Dr. John Murphy-Clark, MD", "NAME_PROVIDER", "[PROVIDER_2]"),
            ("\nFACILITY: ", None), ("Bellevue Hospital Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("462 1st Ave", "GEO_STREET", "[ADDRESS_1]"),
            (", ", None), ("New York", "GEO_CITY", "[CITY_1]"),
            (", NY ", None), ("10016", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPHYSICAL EXAMINATION:\nPatient presenting with 12 hours of acute periumbilical pain migrating to right lower quadrant. Exam by Dr. McBurney-Jones reveals exquisite tenderness at McBurney's point with rebound and guarding; Murphy's sign is negative in right upper quadrant. Verified with Dr. Murphy-Clark.\nCT Abdomen confirms acute non-perforated appendicitis.\n\n", None),
            ("PLAN: Emergency laparoscopic appendectomy scheduled for 06:00 today (09/18/2023).\nSpouse: ", None),
            ("Laura Barton", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Cell: ", None),
            ("212-555-0142", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("Charles McBurney-Jones, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 52: Motor Vehicle Collision, VIN, License Plate, Driver License, SSN
    notes.append(create_note(
        "SYNTH_NOTE_052",
        "Emergency Medicine & Trauma",
        "Emergency Department MVC Trauma Assessment",
        ["unusual_identifiers_telehealth", "signatures_headers_footers"],
        [
            ("EMERGENCY DEPARTMENT MOTOR VEHICLE CRASH ASSESSMENT\n", None),
            ("PATIENT: ", None), ("James 'Rhodey' Rhodes", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("10/06/1968", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | SSN: ", None), ("584-92-0194", "SSN", "[SSN_1]"),
            (" | DRIVER LICENSE: ", None), ("DL-CA-9948201", "LICENSE_STATE", "[LICENSE_1]"),
            ("\nMRN: ", None), ("ED-MVC-774", "MRN", "[MRN_1]"),
            (" | POLICE CRASH REPORT #: ", None), ("CHP-2023-99482", "ID_ACCESSION", "[ID_1]"),
            ("\nADMISSION TIME: ", None), ("11/04/2023 18:40 PST", "DATE", "[DATE_2]", None),
            ("\nEMERGENCY ATTENDING: ", None), ("Dr. Stephen Strange, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nPATIENT VEHICLE VIN: ", None), ("1FA6P8CF5H5994821", "VEHICLE", "[VEHICLE_1]"),
            (" | LICENSE PLATE: ", None), ("CA 9XYZ456", "VEHICLE", "[VEHICLE_2]"),
            ("\n\nCRASH MECHANISM:\nRestrained driver in moderate speed T-bone collision. Airbag deployed. Evaluated by Dr. Strange.\nFAST negative. Cervical spine CT negative for fracture.\nEmergency contact: Friend ", None),
            ("Tony Stark", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Phone: ", None),
            ("310-555-0199", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("Stephen Strange, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 53: Anaphylaxis Emergency, Foley catheter, Digital Signature
    notes.append(create_note(
        "SYNTH_NOTE_053",
        "Emergency Medicine & Trauma",
        "Emergency Department Acute Anaphylaxis Resuscitation",
        ["eponym_vs_doctor_name", "signatures_headers_footers"],
        [
            ("EMERGENCY DEPARTMENT ACUTE RESUSCITATION NOTE\n", None),
            ("PATIENT: ", None), ("Scott 'Ant-Man' Lang", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("09/05/1979", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ED-ANA-88", "MRN", "[MRN_1]"),
            ("\nARRIVAL DATE: ", None), ("08/11/2023 13:10", "DATE", "[DATE_2]", None),
            ("\nEMERGENCY PHYSICIAN: ", None), ("Dr. Frederic Foley-Taylor, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (DEA: ", None), ("BF9948201", "LICENSE_DEA", "[LICENSE_1]"),
            (")\nHOSPITAL: ", None), ("Zuckerberg San Francisco General Hospital", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("San Francisco", "GEO_CITY", "[CITY_1]"),
            (", CA ", None), ("94110", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nPRESENTATION:\nPatient presented with acute anaphylaxis following wasp sting. Severe stridor and hypotension (BP 78/40). Administered IM epinephrine 0.3mg x2, IV methylprednisolone, and diphenhydramine.\nDr. Foley-Taylor placed a standard 16-Fr Foley catheter for strict urine output monitoring.\nPatient stabilized and transferred to observation unit for 12 hours.\nContact: Daughter ", None),
            ("Cassie Lang", "NAME_FAMILY", "[FAMILY_1]"),
            (" (Cell: ", None),
            ("415-555-0167", "PHONE", "[PHONE_1]"),
            (")\nSigned: ", None),
            ("Frederic Foley-Taylor, MD", "NAME_PROVIDER", "[PROVIDER_1]")
        ]
    ))
    
    # Note 54: Sepsis Resuscitation, Multi-date relative interval, Table, MRN
    notes.append(create_note(
        "SYNTH_NOTE_054",
        "Emergency Medicine & Trauma",
        "Emergency Department Severe Sepsis Bundle Record",
        ["tables_and_flowsheets", "relative_timeline_preservation", "signatures_headers_footers"],
        [
            ("EMERGENCY DEPARTMENT SEPSIS BUNDLE FLOWSHEET\n", None),
            ("PATIENT: ", None), ("Arthur 'King' Pendelton", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("04/20/1962", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | MRN: ", None), ("ED-SEP-994", "MRN", "[MRN_1]"),
            ("\nADMISSION DATE: ", None), ("10/01/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nEMERGENCY ATTENDING: ", None), ("Dr. Robert Koch-Stevens, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\n\nSEPSIS RESUSCITATION TABLE:\n", None),
            ("| TIME | INTERVENTION | VALUE / AGENT |\n", None),
            ("| 02:00 | Serum Lactate | 4.2 mmol/L (Elevated) |\n", None),
            ("| 02:15 | Blood Cultures x2 | Accession #: ", None),
            ("BC-2023-994821", "ID_ACCESSION", "[ID_1]"),
            (" |\n| 02:30 | Broad-Spectrum Antibiotics | Vancomycin + Cefepime IV |\n| 02:45 | 30 mL/kg IV Crystalloid | 2.5 Liters Normal Saline infused |\n\n", None),
            ("CLINICAL COURSE:\nAdmitted to ICU on 10/01/2023. Day 2 (10/03/2023) lactate cleared to 1.1 mmol/L. Extubated on Day 3 (10/04/2023). Cleared for discharge on Day 5 (", None),
            ("10/06/2023", "DATE", "[DATE_3]", "%m/%d/%Y"),
            (").\nSigned: ", None),
            ("Robert Koch-Stevens, MD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None),
            ("1774920188", "LICENSE_NPI", "[NPI_1]"),
            (")")
        ]
    ))
    
    # Note 55: Complex Pathology & Trial Subject, Accession IDs, DNA Barcode
    notes.append(create_note(
        "SYNTH_NOTE_055",
        "Pathology & Clinical Research",
        "Molecular Pathology & Precision Oncology Trial Report",
        ["unusual_identifiers_telehealth", "signatures_headers_footers", "tables_and_flowsheets"],
        [
            ("MOLECULAR PATHOLOGY & CLINICAL TRIAL ACCESSION REPORT\n", None),
            ("TRIAL SUBJECT ID: ", None), ("SUBJECT-ONC-2023-0055", "ID_ACCESSION", "[ID_1]"),
            (" | PATIENT: ", None), ("Alexander 'Lex' Luthor-Smith", "NAME_PATIENT", "[PATIENT_1]"),
            (" | DOB: ", None), ("09/19/1973", "DATE", "[DATE_1]", "%m/%d/%Y"),
            (" | SSN: ", None), ("994-82-0193", "SSN", "[SSN_1]"),
            ("\nSPECIMEN COLLECTION DATE: ", None), ("11/10/2023", "DATE", "[DATE_2]", "%m/%d/%Y"),
            ("\nPRINCIPAL PATHOLOGIST: ", None), ("Dr. Rudolf Virchow-Miller, MD, PhD", "NAME_PROVIDER", "[PROVIDER_1]"),
            ("\nINSTITUTE: ", None), ("MD Anderson Cancer Center", "GEO_FACILITY", "[HOSPITAL_1]"),
            (", ", None), ("Houston", "GEO_CITY", "[CITY_1]"),
            (", TX ", None), ("77030", "GEO_ZIP", "[ZIP_1]"),
            ("\n\nMOLECULAR ASSAY LOG:\n", None),
            ("| ASSAY | SPECIMEN ACCESSION | DNA BARCODE | RESULT |\n", None),
            ("| Next-Gen Sequencing | ", None),
            ("PATH-NGS-2023-884", "ID_ACCESSION", "[ID_2]"),
            (" | ", None),
            ("DNA-BAR-994820148", "ID_ACCESSION", "[ID_3]"),
            (" | BRAF V600E Mutation Detected (VAF 34%) |\n| PD-L1 IHC 22C3 | ", None),
            ("PATH-IHC-2023-885", "ID_ACCESSION", "[ID_4]"),
            (" | ", None),
            ("IHC-BAR-994820149", "ID_ACCESSION", "[ID_5]"),
            (" | Tumor Proportion Score (TPS) 85% |\n\n", None),
            ("CLINICAL SIGNIFICANCE: Reviewed by Dr. Virchow-Miller. Patient eligible for trial protocol under Investigational Drug Registry.\nResearch Coordinator: ", None),
            ("713-555-0199", "PHONE", "[PHONE_1]"),
            (" | Email: ", None),
            ("precision-oncology@mdanderson.org", "EMAIL", "[EMAIL_1]"),
            ("\nSigned: ", None),
            ("Rudolf Virchow-Miller, MD, PhD", "NAME_PROVIDER", "[PROVIDER_1]"),
            (" (NPI: ", None),
            ("1994820199", "LICENSE_NPI", "[NPI_1]"),
            (")")
        ]
    ))
    
    return notes


if __name__ == "__main__":
    notes = generate_all_55_notes()
    print(f"Generated {len(notes)} clinical notes.")
    
    # Verify all categories
    categories = set()
    specialties = set()
    tags = set()
    total_entities = 0
    
    for n in notes:
        specialties.add(n["specialty"])
        for t in n["adversarial_tags"]:
            tags.add(t)
        for e in n["entities"]:
            categories.add(e["category"])
            total_entities += 1
            # Verify offset
            assert n["raw_text"][e["start"]:e["end"]] == e["text"], f"Offset error in {n['test_case_id']}"
            
    print(f"Total entities: {total_entities}")
    print(f"Specialties ({len(specialties)}): {specialties}")
    print(f"Adversarial Tags ({len(tags)}): {tags}")
    print(f"Categories ({len(categories)}): {sorted(list(categories))}")
    
    os.makedirs("tests/data", exist_ok=True)
    out_path = "tests/data/annotated_clinical_notes_55.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)
    print(f"Successfully written to {out_path}")
