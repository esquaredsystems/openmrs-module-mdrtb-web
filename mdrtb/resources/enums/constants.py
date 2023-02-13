import enum


class Constants(enum.Enum):

    # Date/Time formats
    DATE_FORMAT_US = 'MM/dd/yyyy'
    DATE_FORMAT_GB = 'dd/MM/yyyy'
    DATE_FORMAT_RU = 'dd.MM.yyyy'
    DATE_FORMAT_SQL = 'yyyy-MM-dd'
    DATETIME_FORMAT_US = 'MM/dd/yyyy hh:mm:ss'
    DATETIME_FORMAT_GB = 'dd/MM/yyyy hh:mm:ss'
    DATETIME_FORMAT_RU = 'dd.MM.yyyy hh:mm:ss'
    DATETIME_FORMAT_SQL = 'yyyy-MM-dd hh:mm:ss'

    # Programs
    DOTS_PROGRAM = "e80fec43-f2b5-45b0-aec1-eaf74be26ff9"
    MDRTB_PROGRAM = "34198d48-0370-102d-b0e3-001ec94a0cc1"

    # Patient Identifiers
    OPENMRS_IDENTIFIER = "8d793bee-c2cc-11de-8d13-0010c6dffd0f"
    SUSPECT_ID = "f3ea5e6d-8b40-4e34-b97d-56577480bfe9"
    DOTS_IDENTIFIER = "8d79403a-c2cc-11de-8d13-0010c6dffd0f"
    MDR_IDENTIFIER = "5c4c9795-2a7a-4757-8585-fba3a7cafa90"
