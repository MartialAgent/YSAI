import os
from dotenv import load_dotenv

load_dotenv()

# PFA Thresholds & Weights
ALPHA = 0.5    # Weight for Similarity deviation (1 - S)
BETA = 0.5     # Weight for Critic deviation
A_SCORE_THRESHOLD = 0.4
GAMMA = 0.2  # Additional weight for confidence in Ascore

# Partial Back-prop Thresholds
I_FACTOR_THRESHOLD = 0.4

# Retry Settings
MAX_FAIL_RETRIES = 2

# Models
WORKER_MODEL = "gpt-4o-mini"
CRITIC_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"
