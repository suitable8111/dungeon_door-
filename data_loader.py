import json
import os

_BASE = os.path.dirname(__file__)


def load_enemies():
    with open(os.path.join(_BASE, 'data', 'enemies.json'), encoding='utf-8') as f:
        return json.load(f)


def load_items():
    with open(os.path.join(_BASE, 'data', 'items.json'), encoding='utf-8') as f:
        return json.load(f)
