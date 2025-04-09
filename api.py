from livekit.agents import llm
from typing import Annotated
import logging
import enum
from db_driver import DatabaseDriver, PatientProfile

logger = logging.getLogger("hospital-agent")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()


def normalize_id_spoken(transcript: str) -> str:
    """Normalize spoken ID input by extracting digits only and padding if needed."""
    digits = "".join(c for c in transcript if c.isdigit())
    return digits  # Adjust .zfill(N) if ID length is fixed

class WorkflowsEnum(enum.Enum):
    """Enum for workflow types."""
    INITIALIZE = "initialize"
    CREATE_PROFILE = "create_profile"
    BOOK_APPOINTMENT = "book_appointment"
    GENERAL_INQUIRY = "general_inquiry"


class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        self._current_profile = None
        self._current_workflow = WorkflowsEnum.INITIALIZE

    @llm.ai_callable(description="Create a new patient profile")
    def create_patient_profile(
        self,
        id_number: Annotated[
            str, llm.TypeInfo(description="The patient's national ID number")
        ],
        mobile_number: Annotated[
            str, llm.TypeInfo(description="The mobile number used for the call")
        ],
        full_name: Annotated[str, llm.TypeInfo(description="The patient's full name")],
    ):
        id_number = normalize_id_spoken(id_number)
        logger.info("Creating patient profile - ID: %s, Name: %s", id_number, full_name)

        result = DB.create_profile(id_number, mobile_number, full_name)
        if result is None:
            return "An error occurred while creating the profile, or the profile already exists."

        self._current_profile = result
        return f"Profile created successfully for patient {result.name}."

    @llm.ai_callable(
        description="Check if a patient profile exists using their national ID"
    )
    def get_patient_profile(
        self,
        id_number: Annotated[
            str, llm.TypeInfo(description="The patient's national ID number")
        ],
    ):
        id_number = normalize_id_spoken(id_number)
        logger.info("Looking up patient profile - ID: %s", id_number)

        result = DB.get_profile_by_id(id_number)
        if result is None:
            return "No patient profile found with the provided national ID."

        self._current_profile = result
        return f"Patient profile found: Name: {result.name}, Mobile Number: {result.mobile_number}."
    
    @llm.ai_callable(
        description="Modify the current workflow based on the user's request/context."
    )
    def get_patient_profile(
        self,
        new_workflow: Annotated[
            WorkflowsEnum, llm.TypeInfo(description="The new workflow to set from WorkflowsEnum")
        ],
    ):
        logger.info("Changing workflow to: %s", new_workflow.name)
        self._current_workflow = new_workflow
        return f"Workflow changed to {new_workflow.name}."

    def has_profile(self):
        return self._current_profile is not None
