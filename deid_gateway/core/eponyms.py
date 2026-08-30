"""
Clinical Ambiguity and Medical Eponym Disambiguation Engine.
Tri-filter logic to protect medical eponyms (e.g. Parkinson's disease, Whipple procedure,
Bell's palsy, Hodgkin lymphoma) while masking doctor/patient names (e.g. Dr. Parkinson, Patient Bell).
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


class EponymDisambiguator:
    """
    Disambiguates medical eponyms from genuine Protected Health Information (PHI).
    
    Tri-Filter Architecture:
    1. Honorific / Role Anchor Override: If title or patient indicator is present -> PHI (MASK).
    2. Lexical Suffix Rule: If followed by medical nouns ('disease', 'syndrome', 'procedure', etc.) -> EPONYM (PROTECT).
    3. Ontology Whitelist: Matches against verified SNOMED CT / UMLS / MeSH clinical eponym database.
    """

    # Rule 1: Anchor patterns that definitively indicate a human provider or patient
    HONORIFIC_PREFIX_PATTERN = re.compile(
        r'\b(?:Dr\.?|Doctor|MD|M\.D\.?|DO|D\.O\.?|NP|N\.P\.?|RN|R\.N\.?|PA|P\.A\.?|Surgeon|'
        r'Attending(?:\s+Physician)?|Resident|Fellow|Physician|Consultant|Specialist|'
        r'Dictated(?:\s+by)?|Dictator|Transcribed(?:\s+by)?|Signed(?:\s+by)?|'
        r'Electronically\s+Signed(?:\s+by)?|Certified(?:\s+by)?|Electronically\s+Certified(?:\s+by)?|'
        r'Provider|Nurse|Genetic\s+Counselor|Counselor|Therapist|Psychologist|Audiologist|Pharmacist|'
        r'Mr\.?|Mrs\.?|Ms\.?|Miss|Patient(?:\s+Name)?|Pt\.?|Spouse|Mother|Father|Brother|Sister|'
        r'Son|Daughter|Child|Guardian|Legal\s+Guardians?|Emergency\s+Contact)[:\s]*$',
        re.IGNORECASE
    )

    HONORIFIC_SUFFIX_PATTERN = re.compile(
        r'^(?:,\s*(?:MD|M\.D\.|DO|D\.O\.|MBBS|PhD|PsyD|CGC|MS,\s*CGC|P\.A\.|PA-C|NP|RN|FACS|FACP|CCP|RDCS|CEP|MS,\s*CEP|CRNA|DPT|OTR/L|MSW|LCSW|Attending|Resident|Fellow|Physician))',
        re.IGNORECASE
    )

    # Candidate text starts with honorific
    CANDIDATE_HONORIFIC_START = re.compile(
        r'^(?:Dr\.?|Doctor|Mr\.?|Mrs\.?|Ms\.?|Miss|Patient|Pt\.?|Attending|Surgeon|Consultant)\b',
        re.IGNORECASE
    )

    # Rule 2: Medical noun suffixes that confirm eponymous clinical meaning
    EPONYM_SUFFIX_PATTERN = re.compile(
        r"^(?:'s|\s+s)?\s+(?:disease|diseases|syndrome|syndromes|palsy|palsies|sign|signs|"
        r"reflex|reflexes|test|tests|score|scores|scale|scales|point|points|maneuver|maneuvers|"
        r"catheter|catheters|line|lines|procedure|procedures|surgery|surgeries|operation|operations|"
        r"lymphoma|lymphomas|thyroiditis|phenomenon|phenomena|chorea|tumor|tumors|tumour|tumours|"
        r"virus|viruses|bacterium|bacteria|area|areas|cells|cell|capsule|capsules|tube|tubes|"
        r"canal|canals|fascia|fascias|gland|glands|node|nodes|bundle|bundles|fibers|fiber|"
        r"triangle|triangles|space|spaces|diverticulum|diverticula|duct|ducts|corpuscle|corpuscles|"
        r"membrane|membranes|patch|patches|plexus|ring|rings|tract|tracts|anomaly|anomalies|"
        r"criteria|classification|staging|position|positions|incision|incisions|repair|repairs|"
        r"resection|resections|shunt|shunts|technique|techniques|method|methods|approach|approaches|"
        r"view|views|law|laws|triad|triads|tetrad|tetrads|pentad|pentads|pattern|patterns|"
        r"complex|complexes|nodule|nodules|spot|spots|organ|organs|body|bodies|colitis|enteritis|"
        r"gastritis|dementia|cirrhosis|angina|sarcoma|sarcomas|arteritis|ophthalmopathy|goiter|"
        r"goitre|myopathy|dystrophy|fracture|fractures|dislocation|dislocations|amputation|graft|flap|"
        r"esophagus|esophageal|colon|ileum|jejunum|artery|vein|nerve|valves|valve)\b",
        re.IGNORECASE
    )

    # Rule 3: Comprehensive SNOMED CT / UMLS clinical eponym whitelist (>80 verified items)
    KNOWN_EPONYMS: Set[str] = {
        # Neurology & Psychiatry
        "parkinson", "parkinson's", "alzheimer", "alzheimer's", "huntington", "huntington's",
        "bell", "bell's", "tourette", "tourette's", "guillain-barre", "guillain-barré",
        "wernicke", "wernicke's", "korsakoff", "korsakoff's", "lou gehrig", "lou gehrig's",
        "horner", "horner's", "charcot-marie-tooth", "charcot", "charcot's", "creutzfeldt-jakob",
        "pick", "pick's", "huntington chorea", "sydenham", "sydenham's",
        # Cardiovascular, Hematology & Oncology
        "hodgkin", "hodgkin's", "non-hodgkin", "non-hodgkin's", "raynaud", "raynaud's",
        "burkitt", "burkitt's", "kaposi", "kaposi's", "osler-weber-rendu", "takayasu", "takayasu's",
        "kawasaki", "purkinje", "bundle of his", "his", "bence jones", "bence-jones", "wilms", "wilms'",
        "ewing", "ewing's", "von willebrand", "fanconi", "fanconi's", "castleman", "castleman's",
        # Gastroenterology & Endocrine
        "crohn", "crohn's", "hashimoto", "hashimoto's", "graves", "graves'", "cushing", "cushing's",
        "addison", "addison's", "barrett", "barrett's", "zollinger-ellison", "zollinger", "mallory-weiss",
        "whipple", "whipple's", "langerhans", "hirschsprung", "hirschsprung's", "meckel", "meckel's",
        "zenker", "zenker's", "boerhaave", "boerhaave's", "plummar-vinson",
        # Signs, Reflexes & Points
        "babinski", "babinski's", "murphy", "murphy's", "mcburney", "mcburney's", "romberg",
        "romberg's", "tinel", "tinel's", "phalen", "phalen's", "kernig", "kernig's",
        "brudzinski", "brudzinski's", "homans", "homans'", "chvostek", "chvostek's", "trousseau",
        "trousseau's", "rovsing", "rovsing's", "cullen", "cullen's", "grey turner", "grey turner's",
        "blumberg", "courvoisier", "hoffman", "hoffmann", "lasegue", "lasegue's", "battle",
        "battle's", "kehr", "kehr's", "gowers", "gowers'", "myerson", "myerson's",
        "lachman", "lachman's", "ponseti",
        # Procedures, Maneuvers & Devices
        "heimlich", "mohs", "billroth", "trendelenburg", "valsalva", "allen", "allen's",
        "dix-hallpike", "epley", "kocher", "pringle", "hartmann", "hartmann's", "nissen",
        "fontan", "norwood", "glenn", "ross", "foley", "swan-ganz", "swan", "hickman", "picc", "halsted",
        # Anatomy & Histology
        "circle of willis", "willis", "fallopian", "eustachian", "loop of henle", "henle",
        "nodes of ranvier", "ranvier", "broca", "broca's", "bowman", "bowman's", "kupffer",
        "schwann", "calot", "calot's", "douglas", "oddi", "vater", "wirsung", "stensen",
        "wharton", "bartholin", "cowper", "skene", "sertoli", "leydig", "auerbach", "meissner", "peyer",
        # Scores, Scales & Systems
        "apgar", "glasgow", "wells", "wells'", "curb-65", "chads", "cha2ds2-vasc", "ranson",
        "child-pugh", "meld", "killip", "nyha", "rankin", "nihss", "braden", "norton",
        "aldrete", "mallampati", "cormack-lehane", "tanner", "gleason", "karnofsky", "ecog",
        "clark", "breslow", "ann arbor", "forrest", "cha2ds2"
    }

    def __init__(self, custom_eponyms: Optional[Set[str]] = None):
        self.whitelist = set(self.KNOWN_EPONYMS)
        if custom_eponyms:
            self.whitelist.update(k.lower() for k in custom_eponyms)

    def is_eponym(
        self,
        candidate_text: str,
        context_before: str,
        context_after: str,
        full_text: str = ""
    ) -> bool:
        """
        Evaluate candidate entity span using the Tri-Filter algorithm.
        
        Returns:
            True if the span is a medical eponym (MUST PROTECT - NOT PHI).
            False if the span is a real human provider/patient (IS PHI - MUST MASK).
        """
        clean_candidate = candidate_text.strip()
        
        # Rule 1a: Check if candidate itself starts with Dr. / Mr. / Patient or contains credentials
        if self.CANDIDATE_HONORIFIC_START.search(clean_candidate):
            return False  # Candidate text is explicitly titled -> It is PHI (MASK)
            
        if any(cred in clean_candidate for cred in [", MD", ", M.D.", ", DO", ", D.O.", ", PhD", ", PsyD", ", CGC", ", FACS", ", MBBS", ", RN", ", NP", ", PA"]):
            if not self.EPONYM_SUFFIX_PATTERN.search(context_after):
                return False

        clean_lower = clean_candidate.lower()
        base_name = clean_lower.rstrip("'s").strip()

        # Rule 1b: Check preceding context for Honorific / Role Anchor
        window_before = context_before[-45:] if len(context_before) > 45 else context_before
        if self.HONORIFIC_PREFIX_PATTERN.search(window_before):
            return False  # Preceded by Dr. / Patient: -> It's a real person (PHI)

        # Rule 1c: Check succeeding context for credential suffix
        window_after = context_after[:35] if len(context_after) > 35 else context_after
        if self.HONORIFIC_SUFFIX_PATTERN.search(window_after):
            return False  # Succeeded by MD / DO -> It's a real person (PHI)

        # Rule 1d: Check if candidate is a multi-word person name (e.g. 'Charles McBurney-Jones') without medical suffix
        words = clean_lower.split()
        if len(words) >= 2 and not any(clean_lower.startswith(prefix) for prefix in [
            "circle of", "loop of", "bundle of", "nodes of", "lou gehrig", "charcot-marie",
            "von willebrand", "bence jones", "creutzfeldt", "mallory-weiss", "zollinger-ellison",
            "osler-weber", "guillain-barr", "dix-hallpike", "grey turner"
        ]):
            if not self.EPONYM_SUFFIX_PATTERN.search(context_after):
                return False

        # Rule 2: Lexical Suffix Rule (immediate medical noun following candidate)
        if self.EPONYM_SUFFIX_PATTERN.search(context_after):
            return True  # Followed by 'disease', 'procedure', 'sign', 'palsy', 'esophagus', etc. -> Protected eponym

        # Rule 3: Ontology Whitelist Matching
        if clean_lower in self.whitelist or base_name in self.whitelist:
            # Check combined immediate phrase (e.g. "classic Hodgkin lymphoma", "Whipple procedure")
            combined_lookahead = (candidate_text + context_after[:50]).lower()
            if any(term in combined_lookahead for term in [
                "disease", "syndrome", "palsy", "sign", "reflex", "test", "score", "scale",
                "point", "maneuver", "catheter", "procedure", "surgery", "operation", "lymphoma",
                "thyroiditis", "phenomenon", "chorea", "fibers", "circle of", "loop of",
                "nodes of", "area", "cells", "capsule", "line", "position", "method", "approach",
                "esophagus", "colon", "ileum", "artery"
            ]):
                return True
            
            # Known multi-word eponyms
            if clean_lower in {"circle of willis", "guillain-barre", "guillain-barré", "lou gehrig", "lou gehrig's", "bundle of his"}:
                return True

            # Clinical context triggers in preceding text
            preceding_lower = window_before.lower()
            if any(hist in preceding_lower for hist in [
                "history of", "hx of", "diagnosed with", "assessment:", "dx:", "positive",
                "negative", "elicited", "classic", "stage", "type", "underwent", "performed", "revealed"
            ]):
                return True

        return False

    def filter_spans(self, spans: List[Any], full_text: str) -> List[Any]:
        """
        Filter out spans that are identified as medical eponyms.
        """
        filtered = []
        for span in spans:
            if isinstance(span, dict):
                start = span["start"]
                end = span["end"]
                category = span.get("category", "")
                text = span.get("text", full_text[start:end])
            else:
                start = getattr(span, "start", 0)
                end = getattr(span, "end", 0)
                category = getattr(span, "category", "")
                text = getattr(span, "text", full_text[start:end])

            # Only evaluate Name / Provider / Patient / Person categories
            if category.upper() in {"PATIENT", "PROVIDER", "DOCTOR", "PHYSICIAN", "PERSON", "NAME", "FAMILY", "NAME_PATIENT", "NAME_PROVIDER"}:
                context_before = full_text[:start]
                context_after = full_text[end:]
                if self.is_eponym(text, context_before, context_after, full_text):
                    # It is an eponym! Do not treat as PHI
                    continue

            filtered.append(span)

        return filtered
