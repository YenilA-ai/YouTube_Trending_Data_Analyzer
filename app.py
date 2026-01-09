import os
import csv
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import processing_core as proc
import charts_core as charts
import exporting_core as exp

class DataStore:
    def __init__(self):
        self.csv_name = "youtube_trending_videos.csv"
        self.csv_path = self._resolve(self.csv_name)
        self.rows = []
        self.loaded = False