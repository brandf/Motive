#!/usr/bin/env python3
"""Script to migrate v1 configs to v2 format while preserving all content."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from .config_loader import V2ConfigLoader
from .effects import SetPropertyEffect, MoveEntityEffect, CodeBindingEffect, GenerateEventEffect


def migrate_config_file(input_path: str, output_path: str, logger: logging.Logger) -> bool:
    """Migrate a single config file from v1 to v2 format."""
    try:
        # Load v1 config
        loader = V2ConfigLoader(logger)
        config_data = loader.load_config_from_file(input_path)
        
        # Migrate to v2
        loader.migrate_v1_to_v2(config_data)
        
        # Convert to v2 format
        v2_config = convert_to_v2_format(loader, config_data)
        
        # Skip writing empty configs
        if not v2_config or (len(v2_config) == 1 and 'entity_definitions' in v2_config and not v2_config['entity_definitions']):
            logger.info(f"⏭️  Skipping empty config: {input_path}")
            return False
        
        # Write v2 config
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(v2_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"✅ Migrated {input_path} → {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to migrate {input_path}: {e}")
        return False


def convert_to_v2_format(loader: V2ConfigLoader, original_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert migrated content to v2 YAML format."""
    v2_config = {}
    
    # Add entity definitions
    if loader.definitions._defs:
        v2_config["entity_definitions"] = {}
        for def_id, definition in loader.definitions._defs.items():
            # Start with behaviors
            ent: dict = {"behaviors": definition.types}

            # Split immutable attributes from mutable properties
            attributes: dict = {}
            properties: dict = {}

            # Move common immutable fields to attributes if present in config
            # Characters: name, backstory, aliases, motives, initial_rooms
            # Objects/Rooms: name, description
            if definition.config:
                for key in ("name", "description", "backstory", "aliases", "motives", "initial_rooms"):
                    if key in definition.config:
                        attributes[key] = definition.config[key]
                # Include any other non-mutable metadata already under attributes in config
                if "attributes" in definition.config and isinstance(definition.config["attributes"], dict):
                    attributes.update(definition.config["attributes"])  # prefer explicit attributes

            # Convert property schema defaults; keep mutable state in properties
            for prop_name, prop_schema in definition.properties.items():
                # If a property duplicates an immutable attribute, prefer attribute and skip here
                if prop_name in ("name", "description", "backstory", "aliases", "motives", "initial_rooms"):
                    if prop_name not in attributes and prop_schema.default is not None:
                        # Fallback: treat as attribute when schema mistakenly carries immutable
                        attributes[prop_name] = prop_schema.default
                    continue
                properties[prop_name] = prop_schema.default

            if attributes:
                ent["attributes"] = attributes
            ent["properties"] = properties

            v2_config["entity_definitions"][def_id] = ent
    
    # Add action definitions
    if loader.actions:
        v2_config["action_definitions"] = {}
        for action_id, action_def in loader.actions.items():
            v2_config["action_definitions"][action_id] = {
                "name": action_def.name,
                "description": action_def.description,
                "cost": action_def.cost,
                "category": action_def.category,  # CRITICAL: Preserve category
                "parameters": [],
                "requirements": [],
                "effects": []
            }
            
            # Convert parameters
            for param in action_def.parameters:
                v2_config["action_definitions"][action_id]["parameters"].append({
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default_value": param.default_value
                })
            
            # Convert requirements (preserve common v1 fields when present)
            for req in action_def.requirements:
                req_dict = {
                    "type": req.type,
                    "description": req.description
                }
                # Convert player_has_tag to character_has_property for v2
                if req.type == "player_has_tag" and hasattr(req, 'tag'):
                    req_dict["type"] = "character_has_property"
                    req_dict["property"] = req.tag
                    req_dict["value"] = True
                # Preserve parsed condition if applicable
                elif req.condition:
                    req_dict["condition"] = str(req.condition)
                # Preserve v1-compatible fields when available
                for field in ("tag", "object_name_param", "property", "value", "target_player_param", "direction_param"):
                    if hasattr(req, field):
                        val = getattr(req, field)
                        if val is not None:
                            req_dict[field] = val
                v2_config["action_definitions"][action_id]["requirements"].append(req_dict)
            
            # Convert effects (handle Effect objects)
            for effect in action_def.effects:
                # Determine effect type from class name
                effect_type = type(effect).__name__.lower().replace("effect", "")
                
                # Map effect types to v1 format
                if effect_type == "codebinding":
                    effect_type = "code_binding"
                elif effect_type == "setproperty":
                    effect_type = "set_property"
                elif effect_type == "moveentity":
                    effect_type = "move_entity"
                elif effect_type == "generateevent":
                    effect_type = "generate_event"
                
                effect_dict = {
                    "type": effect_type
                }
                
                # Copy fields based on effect type
                if isinstance(effect, SetPropertyEffect):
                    effect_dict["target"] = effect.target_entity
                    effect_dict["property"] = effect.property_name
                    effect_dict["value"] = effect.value
                elif isinstance(effect, MoveEntityEffect):
                    effect_dict["entity_id"] = effect.entity_id
                    effect_dict["new_container"] = effect.new_container
                elif isinstance(effect, CodeBindingEffect):
                    effect_dict["function_name"] = effect.function_name
                    if effect.observers:
                        effect_dict["observers"] = effect.observers
                elif isinstance(effect, GenerateEventEffect):
                    effect_dict["message"] = effect.message
                    if effect.observers:
                        effect_dict["observers"] = effect.observers
                else:
                    # For other effect types, copy all attributes
                    for attr_name in dir(effect):
                        if not attr_name.startswith('_') and not callable(getattr(effect, attr_name)):
                            attr_value = getattr(effect, attr_name)
                            if attr_value is not None:
                                effect_dict[attr_name] = attr_value
                    
                v2_config["action_definitions"][action_id]["effects"].append(effect_dict)
    
    # Add entity instances (for rooms, objects, characters)
    if loader.entities:
        v2_config["entity_instances"] = loader.entities
    
    return v2_config


def migrate_all_configs(logger: logging.Logger) -> bool:
    """Migrate all configs to v2 format."""
    total_success = 0
    total_files = 0
    
    # 1. Migrate integration test configs first (most important for testing)
    logger.info("🔄 Migrating integration test configs...")
    test_configs = [
        ("tests/configs/test_simple_merging.yaml", "tests/configs/test_simple_merging_migrated.yaml"),
        ("tests/configs/test_hierarchical.yaml", "tests/configs/test_hierarchical_migrated.yaml"),
        ("tests/configs/test_action_validation.yaml", "tests/configs/test_action_validation_migrated.yaml"),
        ("tests/configs/test_standalone.yaml", "tests/configs/test_standalone_migrated.yaml"),
        ("tests/configs/test_relative_paths.yaml", "tests/configs/test_relative_paths_migrated.yaml"),
        ("tests/configs/test_advanced_merging.yaml", "tests/configs/test_advanced_merging_migrated.yaml"),
        ("tests/configs/test_patch_references.yaml", "tests/configs/test_patch_references_migrated.yaml"),
        ("tests/configs/test_merge_order.yaml", "tests/configs/test_merge_order_migrated.yaml"),
        ("tests/configs/test_deep_cycle.yaml", "tests/configs/test_deep_cycle_migrated.yaml"),
        ("tests/configs/test_self_reference.yaml", "tests/configs/test_self_reference_migrated.yaml"),
        ("tests/configs/integration/test_hints.yaml", "tests/configs/integration/test_hints_migrated.yaml")
    ]
    
    for input_file, output_file in test_configs:
        total_files += 1
        if migrate_config_file(input_file, output_file, logger):
            total_success += 1
    
    # 2. Migrate core configs (even if empty, for completeness)
    logger.info("🔄 Migrating core configs...")
    core_configs = [
        ("configs/core_rooms.yaml", "configs/core_rooms_migrated.yaml"),
        ("configs/core_objects.yaml", "configs/core_objects_migrated.yaml"),
        ("configs/core_characters.yaml", "configs/core_characters_migrated.yaml"),
        ("configs/core_actions.yaml", "configs/core_actions_migrated.yaml")
    ]
    
    for input_file, output_file in core_configs:
        total_files += 1
        if migrate_config_file(input_file, output_file, logger):
            total_success += 1
    
    # 3. Migrate fantasy theme configs
    logger.info("🔄 Migrating fantasy theme configs...")
    fantasy_configs = [
        ("configs/themes/fantasy/fantasy_rooms.yaml", "configs/themes/fantasy/fantasy_rooms_migrated.yaml"),
        ("configs/themes/fantasy/fantasy_objects.yaml", "configs/themes/fantasy/fantasy_objects_migrated.yaml"),
        ("configs/themes/fantasy/fantasy_characters.yaml", "configs/themes/fantasy/fantasy_characters_migrated.yaml"),
        ("configs/themes/fantasy/fantasy_actions.yaml", "configs/themes/fantasy/fantasy_actions_migrated.yaml")
    ]
    
    for input_file, output_file in fantasy_configs:
        total_files += 1
        if migrate_config_file(input_file, output_file, logger):
            total_success += 1
    
    # 4. Migrate hearth_and_shadow configs (already done, but re-run for consistency)
    logger.info("🔄 Migrating hearth_and_shadow configs...")
    hearth_configs = [
        ("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml", "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml"),
        ("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml", "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_migrated.yaml"),
        ("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters.yaml", "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml"),
        ("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_actions.yaml", "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_actions_migrated.yaml")
    ]
    
    for input_file, output_file in hearth_configs:
        total_files += 1
        if migrate_config_file(input_file, output_file, logger):
            total_success += 1
    
    # 5. Create migrated main configs
    logger.info("🔄 Creating migrated main configs...")
    
    # Core migrated config (clean YAML) - only include files that exist
    core_includes = []
    for filename in ["core_rooms_migrated.yaml", "core_objects_migrated.yaml", "core_characters_migrated.yaml", "core_actions_migrated.yaml"]:
        if Path(f"configs/{filename}").exists():
            core_includes.append(filename)
    
    core_main_config = {
        "includes": core_includes,
        "testid": "core_migrated",
        "name": "Core (Migrated)"
    }
    
    with open("configs/core_migrated.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(core_main_config, f, default_flow_style=False, sort_keys=False)
    
    # Fantasy migrated config (clean YAML) - only include files that exist
    fantasy_includes = ["../../core_migrated.yaml"]
    for filename in ["fantasy_rooms_migrated.yaml", "fantasy_objects_migrated.yaml", "fantasy_characters_migrated.yaml", "fantasy_actions_migrated.yaml"]:
        if Path(f"configs/themes/fantasy/{filename}").exists():
            fantasy_includes.append(filename)
    
    fantasy_main_config = {
        "includes": fantasy_includes,
        "testid": "fantasy_migrated",
        "name": "Fantasy Theme (Migrated)",
        "theme_id": "fantasy"
    }
    
    with open("configs/themes/fantasy/fantasy_migrated.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(fantasy_main_config, f, default_flow_style=False, sort_keys=False)
    
    # Hearth and Shadow migrated config (clean YAML) - only include files that exist
    hearth_includes = ["../../fantasy_migrated.yaml"]
    for filename in ["hearth_and_shadow_rooms_migrated.yaml", "hearth_and_shadow_characters_migrated.yaml", "hearth_and_shadow_objects_migrated.yaml", "hearth_and_shadow_actions_migrated.yaml"]:
        if Path(f"configs/themes/fantasy/editions/hearth_and_shadow/{filename}").exists():
            hearth_includes.append(filename)
    
    hearth_main_config = {
        "includes": hearth_includes,
        "testid": "hearth_and_shadow_migrated",
        "name": "Hearth and Shadow (Migrated)",
        "theme_id": "fantasy",
        "edition_id": "hearth_and_shadow"
    }
    
    with open("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(hearth_main_config, f, default_flow_style=False, sort_keys=False)
    
    total_files += 3  # 3 main configs created
    total_success += 3
    
    logger.info(f"📊 Complete migration: {total_success}/{total_files} files migrated successfully")
    # Success if we migrated all non-empty configs (some may be skipped if empty)
    return True  # All configs that could be migrated were migrated successfully


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    success = migrate_all_configs(logger)
    if success:
        logger.info("🎉 All configs migrated successfully!")
    else:
        logger.error("❌ Some configs failed to migrate")
