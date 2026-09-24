#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

import json
import os
from pathlib import Path


class PortableConfig:
    def __init__(self, program_root, config_path=None):
        self.program_root = Path(program_root).resolve()
        self.path = (
            Path(config_path).expanduser()
            if config_path is not None
            else self.program_root / "config" / "linspectacles.json"
        )
        self.data = {
            "lazy_load_utilities": True,
            "disabled_applets": [],
            "applet_order": [],
            "metadata_font": "",
            "hidden_columns": {},
            "module_states": {},
            "module_dashboard_visibility": {},
            "module_order": [],
        }
        self.load()

    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return
            if isinstance(raw.get("lazy_load_utilities"), bool):
                self.data["lazy_load_utilities"] = raw["lazy_load_utilities"]
            for key in ("disabled_applets", "applet_order"):
                value = raw.get(key)
                if isinstance(value, list) and all(isinstance(item, str) for item in value):
                    self.data[key] = value
            metadata_font = raw.get("metadata_font")
            if isinstance(metadata_font, str):
                self.data["metadata_font"] = metadata_font
            hidden_columns = raw.get("hidden_columns")
            if isinstance(hidden_columns, dict):
                cleaned = {}
                for applet_id, columns in hidden_columns.items():
                    if isinstance(applet_id, str) and isinstance(columns, list) and all(isinstance(item, str) for item in columns):
                        cleaned[applet_id] = columns
                self.data["hidden_columns"] = cleaned
            module_order = raw.get("module_order")
            if isinstance(module_order, list) and all(isinstance(item, str) for item in module_order):
                self.data["module_order"] = module_order
            module_states = raw.get("module_states")
            if isinstance(module_states, dict):
                cleaned_states = {}
                for module_id, enabled in module_states.items():
                    if isinstance(module_id, str) and isinstance(enabled, bool):
                        cleaned_states[module_id] = enabled
                self.data["module_states"] = cleaned_states
            module_dashboard_visibility = raw.get("module_dashboard_visibility")
            if isinstance(module_dashboard_visibility, dict):
                cleaned_visibility = {}
                for module_id, visible in module_dashboard_visibility.items():
                    if isinstance(module_id, str) and isinstance(visible, bool):
                        cleaned_visibility[module_id] = visible
                self.data["module_dashboard_visibility"] = cleaned_visibility
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, self.path)
            return True
        except OSError:
            return False

    @property
    def lazy_load_utilities(self):
        return bool(self.data.get("lazy_load_utilities", True))

    @lazy_load_utilities.setter
    def lazy_load_utilities(self, value):
        self.data["lazy_load_utilities"] = bool(value)
        self.save()

    @property
    def disabled_applets(self):
        return set(self.data.get("disabled_applets", []))

    def set_applet_enabled(self, applet_id, enabled):
        disabled = self.disabled_applets
        if enabled:
            disabled.discard(applet_id)
        else:
            disabled.add(applet_id)
        self.data["disabled_applets"] = sorted(disabled)
        self.save()

    @property
    def applet_order(self):
        return list(self.data.get("applet_order", []))

    @applet_order.setter
    def applet_order(self, value):
        self.data["applet_order"] = list(value)
        self.save()

    @property
    def metadata_font(self):
        return str(self.data.get("metadata_font", ""))

    @metadata_font.setter
    def metadata_font(self, value):
        self.data["metadata_font"] = str(value or "")
        self.save()

    def hidden_columns_for(self, applet_id):
        mapping = self.data.get("hidden_columns", {})
        value = mapping.get(str(applet_id), []) if isinstance(mapping, dict) else []
        return list(value) if isinstance(value, list) else []

    def set_hidden_columns(self, applet_id, columns):
        mapping = self.data.get("hidden_columns", {})
        if not isinstance(mapping, dict):
            mapping = {}
        mapping = dict(mapping)
        cleaned = [str(item) for item in (columns or [])]
        if cleaned:
            mapping[str(applet_id)] = cleaned
        else:
            mapping.pop(str(applet_id), None)
        self.data["hidden_columns"] = mapping
        self.save()

    @property
    def module_order(self):
        return list(self.data.get("module_order", []))

    @module_order.setter
    def module_order(self, value):
        self.data["module_order"] = list(value)
        self.save()

    def module_enabled(self, module_id, default=False):
        mapping = self.data.get("module_states", {})
        if isinstance(mapping, dict) and str(module_id) in mapping:
            return bool(mapping[str(module_id)])
        return bool(default)

    def set_module_enabled(self, module_id, enabled):
        mapping = self.data.get("module_states", {})
        if not isinstance(mapping, dict):
            mapping = {}
        mapping = dict(mapping)
        mapping[str(module_id)] = bool(enabled)
        self.data["module_states"] = mapping
        self.save()

    def forget_module_state(self, module_id):
        mapping = self.data.get("module_states", {})
        if not isinstance(mapping, dict) or str(module_id) not in mapping:
            return
        mapping = dict(mapping)
        mapping.pop(str(module_id), None)
        self.data["module_states"] = mapping
        self.save()

    def module_dashboard_visible(self, module_id, default=True):
        mapping = self.data.get("module_dashboard_visibility", {})
        if isinstance(mapping, dict) and str(module_id) in mapping:
            return bool(mapping[str(module_id)])
        return bool(default)

    def set_module_dashboard_visible(self, module_id, visible):
        mapping = self.data.get("module_dashboard_visibility", {})
        if not isinstance(mapping, dict):
            mapping = {}
        mapping = dict(mapping)
        mapping[str(module_id)] = bool(visible)
        self.data["module_dashboard_visibility"] = mapping
        self.save()

    def forget_module_dashboard_visibility(self, module_id):
        mapping = self.data.get("module_dashboard_visibility", {})
        if not isinstance(mapping, dict) or str(module_id) not in mapping:
            return
        mapping = dict(mapping)
        mapping.pop(str(module_id), None)
        self.data["module_dashboard_visibility"] = mapping
        self.save()


