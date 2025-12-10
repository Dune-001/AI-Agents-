import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = "gpt-3.5-turbo"

    @classmethod
    def validate(cls):
        '''validating configuration'''
        if not cls.OPENAI_API_KEY:
            raise ValueError('OPENAI_API_KEY not found in .env file')
        return True