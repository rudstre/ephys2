'''
Global settings for the application (per-process)
'''
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
	# Backend
	mpi_enabled: bool = True
	# GUI
	gui_profiling_on: bool = False
	gui_tag: Optional[str] = None
	# Both
	debug_on: bool = False

global_settings = Settings()