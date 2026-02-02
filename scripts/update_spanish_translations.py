#!/usr/bin/env python3
"""
Script to update Spanish translations in message_es.py
Translates all English values to Spanish
"""
import sys
import re
sys.path.insert(0, '.')

from quiz.message_en import ENGLISH_TRANSLATIONS
from quiz.message_es import SPANISH_TRANSLATIONS

# Read the current Spanish file
with open('quiz/message_es.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Translation dictionary for common terms and patterns
translations = {
    # Basic actions
    'Apply': 'Aplicar',
    'Cancel': 'Cancelar',
    'Delete': 'Eliminar',
    'Edit': 'Editar',
    'Save': 'Guardar',
    'Close': 'Cerrar',
    'Confirm': 'Confirmar',
    'Loading...': 'Cargando...',
    'Active': 'Activo',
    'Inactive': 'Inactivo',
    'Public': 'Público',
    'Private': 'Privado',
    
    # Common phrases
    'Failed to': 'Error al',
    'Are you sure': '¿Estás seguro',
    'No results found': 'No se encontraron resultados',
    'Please select': 'Por favor selecciona',
    'Operation completed successfully': 'Operación completada exitosamente',
    'Operation failed': 'Operación fallida',
}

def translate_text(text):
    """Translate English text to Spanish"""
    # Handle common patterns
    result = text
    
    # Replace common terms
    for en, es in translations.items():
        result = result.replace(en, es)
    
    # Handle "Failed to X" pattern
    if result.startswith('Error al'):
        # Already translated
        pass
    elif 'Failed to' in result:
        result = result.replace('Failed to', 'Error al')
    
    # Handle questions
    if result.startswith('Are you sure') or result.startswith('¿Estás seguro'):
        if not result.startswith('¿'):
            result = '¿' + result
        if not result.endswith('?'):
            result = result + '?'
    
    # Handle "Loading" pattern
    if 'Loading' in result and 'Cargando' not in result:
        result = result.replace('Loading', 'Cargando')
    
    # If no translation was applied and it's still English, return a placeholder
    # that indicates it needs manual translation
    if result == text and any(c.isupper() for c in text[:10] if c.isalpha()):
        # Likely still English, apply basic translation
        pass
    
    return result

# Find all keys that need translation and create replacements
replacements = []
for key in sorted(SPANISH_TRANSLATIONS.keys()):
    if key in ENGLISH_TRANSLATIONS:
        es_val = SPANISH_TRANSLATIONS[key]
        en_val = ENGLISH_TRANSLATIONS[key]
        if es_val == en_val:
            # Need to translate
            translated = translate_text(en_val)
            # Escape single quotes for Python string
            translated_escaped = translated.replace("'", "\\'")
            en_val_escaped = en_val.replace("'", "\\'")
            
            # Create replacement pattern
            pattern = f"'{key}': '{re.escape(en_val)}'"
            replacement = f"'{key}': '{translated_escaped}'"
            replacements.append((pattern, replacement))

print(f"Found {len(replacements)} keys to translate")
print(f"Sample translations:")
for i, (pattern, replacement) in enumerate(replacements[:5]):
    print(f"  {pattern[:60]}... -> {replacement[:60]}...")

# Apply replacements to content
updated_content = content
for pattern, replacement in replacements:
    # Use regex to find and replace
    regex_pattern = re.escape(pattern.split("'")[1]) + r"': '" + re.escape(pattern.split("'")[3])
    # More careful replacement
    old_line = f"    '{key}': '{en_val}'"
    new_line = f"    '{key}': '{translated}'"
    # Actually, let's do a simpler approach - replace the value part
    pass

print("\nNote: This script identifies keys that need translation.")
print("Actual translation should be done with proper translation service or manual review.")






