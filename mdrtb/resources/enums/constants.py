import enum


class Constants(enum.Enum):
    # Date/Time formats
    DATE_FORMAT_US = "MM/dd/yyyy"
    DATE_FORMAT_GB = "dd/MM/yyyy"
    DATE_FORMAT_RU = "dd.MM.yyyy"
    DATE_FORMAT_SQL = "yyyy-MM-dd"
    DATETIME_FORMAT_US = "MM/dd/yyyy hh:mm:ss"
    DATETIME_FORMAT_GB = "dd/MM/yyyy hh:mm:ss"
    DATETIME_FORMAT_RU = "dd.MM.yyyy hh:mm:ss"
    DATETIME_FORMAT_SQL = "yyyy-MM-dd hh:mm:ss"

    # Programs
    DOTS_PROGRAM = "e80fec43-f2b5-45b0-aec1-eaf74be26ff9"
    MDRTB_PROGRAM = "34198d48-0370-102d-b0e3-001ec94a0cc1"

    # Patient Identifiers
    OPENMRS_IDENTIFIER = "8d793bee-c2cc-11de-8d13-0010c6dffd0f"
    SUSPECT_IDENTIFIER = "f3ea5e6d-8b40-4e34-b97d-56577480bfe9"
    DOTS_IDENTIFIER = "8d79403a-c2cc-11de-8d13-0010c6dffd0f"
    MDR_IDENTIFIER = "5c4c9795-2a7a-4757-8585-fba3a7cafa90"

    # Locals
    EN = "English (United States)"
    EN_GB = "English (United Kingdom)"
    ES = "Spanish"
    FR = "French"
    IT = "Italian"
    PT = "Portuguese"
    RU = "Russian"
    TJ = "Tajik"

    # Location attribute Types
    LEVEL = "6b738ed1-78b3-4cdb-81f6-7fdc5da20a3d"

    # Order Types
    DRUG = "33ccf820-0370-102d-b0e3-001ec94a0cc1"
    DRUG_ORDER = "131168f4-15f5-102d-96e4-000c29c2a5d7"
    TEST_ORDER = "52a447d3-a64a-11e3-9aeb-50e549534c5e"

    # Care Setting
    OUTPATIENT = "6f0c9a92-6f24-11e3-af88-005056821db0"
    INPATIENT = "c365e560-c3ec-11e3-9c1a-0800200c9a66"

    # Sample status
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COLLECTED = "COLLECTED"
    PROCESSED = "PROCESSED"

    COUNTRY = "Таджикистан (Точикистон)"

    # CLM
    COMMONLAB_LAB_REFERENCE_ATTRIBUTE_TYPE_CMN_TEST = (
        "475932eb-51a0-0c66-006f-6823f161c7f2"
    )
    COMMONLAB_LAB_REFERENCE_ATTRIBUTE_TYPE_LJ_TEST = (
        "bf91fd17-1d02-d204-db7e-0b5cb42f031e"
    )
    COMMONLAB_LAB_REFERENCE_ATTRIBUTE_TYPE_MGIT_TEST = (
        "886e914d-8451-8cc2-8974-1994a4baa542"
    )

    SPECIMEN_SOURCE = "5baeba18-9bf1-95ad-9a51-f56f59403436"
    TUBERCILOSIS_SAMPLE_SOURCE = "007aaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    DATE_OF_REQUEST_FOR_LABORATORY_INVESTIGATION = (
        "ce49756b-929b-3920-f1a1-3fd205440576"
    )
    COMMON_TEST = "05aaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    DST_MGIT = "07aaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    DST_LJ = "08aaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    # Concept name types
    FULLY_SPECIFIED = "FULLY_SPECIFIED"
    SHORT = "SHORT"

    # Encounter role Unknown
    ENCOUNTER_ROLE_UNKNOWN = "a0b03050-c99b-11e0-9572-0800200c9a66"