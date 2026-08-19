import random
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class QuestionBank:
    """
    Manages the questions asked during the asynchronous verification process.
    """
    QUESTIONS = {
        "OCCUPATION": "Could you please state your current occupation?",
        "CITY": "Which city are you currently residing in?",
        "PHONE": "Could you confirm the last 4 digits of your registered mobile number?",
        "BIRTH_YEAR": "Could you please state your year of birth?",
        "MOTHER_NAME": "Could you please tell me your mother's first name?"
    }

    @classmethod
    def get_three_random_questions(cls) -> List[Tuple[str, str]]:
        """
        Returns a list of 3 random tuples: (Question ID, Question Text)
        """
        selected_keys = random.sample(list(cls.QUESTIONS.keys()), 3)
        return [(key, cls.QUESTIONS[key]) for key in selected_keys]

    @classmethod
    def validate_answer(cls, question_type: str, expected_data: Dict, user_answer: str) -> bool:
        """
        Validates the user's answer against expected background data.
        In a production system, this would use an LLM or fuzzy match against structured data.
        For now, we return a mock True to allow the flow to proceed.
        """
        # Example: LLM tool can submit the answer here, we validate it, and return True/False.
        # We do NOT return the correct answer to the LLM.
        logger.info(f"Validating answer for {question_type}: {user_answer}")
        return True

question_bank = QuestionBank()
