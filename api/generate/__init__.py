"""
This module contains the configuration classes for AutoGPT.
"""
#from config.ai_config import AIConfig
from generate.auto_generate import multiple_generate, gen_response_json, gen_response_string
from generate.relationship import Relation

__all__ = [
    "multiple_generate",
    "gen_response_json",
    "gen_response_string",
    "Relation",
]