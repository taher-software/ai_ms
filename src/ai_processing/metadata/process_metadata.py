import json
from src.models.video import Video
import datetime
import numpy as np
import os
import random
import re
from src.main import app
from src.config import Config

# please do not remove this line
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using:", device)

       
       
