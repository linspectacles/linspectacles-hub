#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

import json
import os
from pathlib import Path

from .paths import MANUAL_LOCATION_VALUES, MANUAL_SHARED

COMPONENT_SOURCE_MANUAL = "manual"
COMPONENT_SOURCE_MANAGED = "managed"
COMPONENT_SOURCE_VALUES = {COMPONENT_SOURCE_MANUAL, COMPONENT_SOURCE_MANAGED}


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
            "manual_component_location": MANUAL_SHARED,
            "manual_component_custom_root": "",
            "manual_component_location_confirmed": False,
            "preferred_component_source": COMPONENT_SOURCE_MANUAL,
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
            location = str(raw.get("manual_component_location", MANUAL_SHARED)).strip().lower()
            if location in MANUAL_LOCATION_VALUES:
                self.data["manual_component_location"] = location
            custom_root = raw.get("manual_component_custom_root")
            if isinstance(custom_root, str):
                self.data["manual_component_custom_root"] = custom_root
            confirmed = raw.get("manual_component_location_confirmed")
            if isinstance(confirmed, bool):
                self.data["manual_component_location_confirmed"] = confirmed
            preferred_source = str(raw.get("preferred_component_source", COMPONENT_SOURCE_MANUAL)).strip().lower()
            if preferred_source in COMPONENT_SOURCE_VALUES:
                self.data["preferred_component_source"] = preferred_source
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

    def applet_enabled(self, instance_id, logical_id=None):
        disabled = self.disabled_applets
        return str(instance_id) not in disabled and (logical_id is None or str(logical_id) not in disabled)

    def set_applet_enabled(self, instance_id, enabled, logical_id=None):
        disabled = self.disabled_applets
        if enabled:
            disabled.discard(str(instance_id))
            if logical_id is not None:
                disabled.discard(str(logical_id))
        else:
            disabled.add(str(instance_id))
        self.data["disabled_applets"] = sorted(disabled)
        self.save()

    def migrate_legacy_applet_settings(self, manifests):
        disabled = self.disabled_applets
        logical_ids = {m.applet_id for m in manifests}
        changed = False
        for logical_id in list(disabled & logical_ids):
            disabled.discard(logical_id)
            for manifest in manifests:
                if manifest.applet_id == logical_id:
                    disabled.add(manifest.instance_id)
            changed = True
        if changed:
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

    def module_state_is_explicit(self, module_id):
        """Return whether logical Hub Module enablement was explicitly stored."""
        mapping = self.data.get("module_states", {})
        return isinstance(mapping, dict) and str(module_id) in mapping

    def module_enabled(self, module_id, default=False, logical_id=None):
        """Return logical Hub Module enablement.

        ``logical_id`` is accepted for source compatibility with older internal
        callers that passed ``instance_id, default, logical_id``.  0.1.8 stores
        one enablement value per logical module ID; the global User/
        Package-managed preference selects the physical implementation.
        """
        key = str(logical_id if logical_id is not None else module_id)
        mapping = self.data.get("module_states", {})
        if isinstance(mapping, dict) and key in mapping:
            return bool(mapping[key])
        return bool(default)

    def set_module_enabled(self, module_id, enabled, logical_id=None):
        """Persist one enablement value for the logical Hub Module."""
        key = str(logical_id if logical_id is not None else module_id)
        mapping = self.data.get("module_states", {})
        if not isinstance(mapping, dict):
            mapping = {}
        mapping = dict(mapping)
        mapping[key] = bool(enabled)
        self.data["module_states"] = mapping
        self.save()

    def resolve_applet_presentation(self, manifests):
        """Resolve ordinary Hub presentation without hiding discovery state.

        If both User and Package-managed enabled copies of the same logical
        applet exist, only the globally preferred ownership class is returned
        for normal navigation. Configuration and discovery remain
        instance-complete. Versions are never compared.
        """
        groups = {}
        order = []
        for manifest in manifests:
            if manifest.applet_id not in groups:
                groups[manifest.applet_id] = []
                order.append(manifest.applet_id)
            groups[manifest.applet_id].append(manifest)
        resolved = []
        for logical_id in order:
            candidates = groups[logical_id]
            origins = {candidate.origin for candidate in candidates}
            if len(origins) <= 1:
                resolved.extend(candidates)
                continue
            preferred = [
                candidate for candidate in candidates
                if candidate.origin == self.preferred_component_source
            ]
            resolved.extend(preferred or candidates)
        return resolved

    def resolve_module_enablement(self, manifests):
        """Resolve one physical implementation for each enabled logical module.

        Enablement belongs to the logical module ID.  If both User and
        Package-managed implementations exist, the global preferred component
        source selects the implementation.  Versions are never compared.
        """
        groups = {}
        order = []
        for manifest in manifests:
            if manifest.module_id not in groups:
                groups[manifest.module_id] = []
                order.append(manifest.module_id)
            groups[manifest.module_id].append(manifest)

        enabled = set()
        for logical_id in order:
            candidates = groups[logical_id]
            default_enabled = any(bool(candidate.enabled_by_default) for candidate in candidates)
            if not self.module_enabled(logical_id, default_enabled):
                continue
            preferred = [
                candidate for candidate in candidates
                if candidate.origin == self.preferred_component_source
            ]
            pool = preferred or candidates
            # There is at most one physical copy per logical ID per source.
            # In the unlikely event of malformed duplicate source records, keep
            # discovery honest but do not load more than one implementation.
            selected = pool[0] if pool else None
            if selected is not None:
                enabled.add(selected.instance_id)
        return enabled, set()

    def disable_other_module_instances(self, logical_id, keep_instance_id, manifests):
        """0.1.7 compatibility no-op.

        Module enablement is logical in 0.1.8; physical implementation choice
        is controlled by the global component-source preference.
        """
        return None

    def forget_module_state(self, module_id):
        mapping = self.data.get("module_states", {})
        if not isinstance(mapping, dict) or str(module_id) not in mapping:
            return
        mapping = dict(mapping)
        mapping.pop(str(module_id), None)
        self.data["module_states"] = mapping
        self.save()

    def migrate_legacy_module_states(self, manifests):
        """Collapse pre-0.1.8 per-instance module state into logical state.

        Any explicitly enabled copy keeps the logical module enabled. If one or
        more old instance states exist and none is enabled, the logical module
        remains disabled. This prevents a source-preference change from
        unexpectedly activating a module during upgrade.
        """
        mapping = self.data.get("module_states", {})
        if not isinstance(mapping, dict):
            return
        mapping = dict(mapping)
        by_logical = {}
        for manifest in manifests:
            by_logical.setdefault(manifest.module_id, []).append(manifest)

        changed = False
        for logical_id, candidates in by_logical.items():
            logical_present = logical_id in mapping
            instance_keys = [candidate.instance_id for candidate in candidates if candidate.instance_id in mapping]
            if logical_present:
                # Logical state is already authoritative; discard stale physical
                # state from older releases.
                for key in instance_keys:
                    mapping.pop(key, None)
                    changed = True
                continue
            if not instance_keys:
                continue
            mapping[logical_id] = any(bool(mapping[key]) for key in instance_keys)
            for key in instance_keys:
                mapping.pop(key, None)
            changed = True

        if changed:
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

    @property
    def manual_component_location(self):
        value = str(self.data.get("manual_component_location", MANUAL_SHARED)).strip().lower()
        return value if value in MANUAL_LOCATION_VALUES else MANUAL_SHARED

    @property
    def manual_component_custom_root(self):
        return str(self.data.get("manual_component_custom_root", ""))

    @property
    def manual_component_location_confirmed(self):
        return bool(self.data.get("manual_component_location_confirmed", False))


    @property
    def preferred_component_source(self):
        value = str(self.data.get("preferred_component_source", COMPONENT_SOURCE_MANUAL)).strip().lower()
        return value if value in COMPONENT_SOURCE_VALUES else COMPONENT_SOURCE_MANUAL

    @preferred_component_source.setter
    def preferred_component_source(self, value):
        value = str(value or COMPONENT_SOURCE_MANUAL).strip().lower()
        if value not in COMPONENT_SOURCE_VALUES:
            raise ValueError("Unsupported preferred component source.")
        self.data["preferred_component_source"] = value
        self.save()

    def set_manual_component_location(self, location, custom_root="", confirmed=True):
        location = str(location or MANUAL_SHARED).strip().lower()
        if location not in MANUAL_LOCATION_VALUES:
            raise ValueError("Unsupported manual component location.")
        self.data["manual_component_location"] = location
        self.data["manual_component_custom_root"] = str(custom_root or "").strip()
        self.data["manual_component_location_confirmed"] = bool(confirmed)
        self.save()
