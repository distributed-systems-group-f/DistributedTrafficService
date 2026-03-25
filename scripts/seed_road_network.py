#!/usr/bin/env python3
"""Standalone seed script for road network segments."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.seed_data.road_network import seed
import asyncio

if __name__ == "__main__":
    asyncio.run(seed())
