#!/usr/bin/env python3
"""
Script to translate English keys in message_es.py to Spanish
"""
import sys
sys.path.insert(0, '.')

from quiz.message_en import ENGLISH_TRANSLATIONS
from quiz.message_es import SPANISH_TRANSLATIONS

# Simple translation dictionary for common terms
COMMON_TRANSLATIONS = {
    'Apply': 'Aplicar',
    'Cancel': 'Cancelar',
    'Delete': 'Eliminar',
    'Edit': 'Editar',
    'Save': 'Guardar',
    'Close': 'Cerrar',
    'Confirm': 'Confirmar',
    'Loading...': 'Cargando...',
    'Failed to': 'Error al',
    'Success': 'Éxito',
    'Error': 'Error',
    'Warning': 'Advertencia',
    'Required': 'Requerido',
    'Optional': 'Opcional',
    'Active': 'Activo',
    'Inactive': 'Inactivo',
    'Public': 'Público',
    'Private': 'Privado',
    'Yes': 'Sí',
    'No': 'No',
}

def translate_to_spanish(text):
    """Simple translation helper - in production, use proper translation API"""
    # This is a placeholder - actual translations should be done properly
    # For now, we'll use a basic approach
    text_lower = text.lower()
    
    # Common patterns
    if text.startswith('Failed to'):
        return text.replace('Failed to', 'Error al')
    if text.startswith('Are you sure'):
        return text.replace('Are you sure', '¿Estás seguro')
    if 'Loading' in text:
        return text.replace('Loading', 'Cargando')
    if 'Success' in text:
        return text.replace('Success', 'Éxito')
    
    return text  # Return as-is for now, will need proper translation

# Find all keys that are still in English
translations_to_update = {}
for key in SPANISH_TRANSLATIONS.keys():
    if key in ENGLISH_TRANSLATIONS:
        es_val = SPANISH_TRANSLATIONS[key]
        en_val = ENGLISH_TRANSLATIONS[key]
        if es_val == en_val:
            # This key needs translation
            translations_to_update[key] = en_val

print(f"Found {len(translations_to_update)} keys that need translation")
print("\nSample keys that need translation:")
for i, key in enumerate(sorted(list(translations_to_update.keys()))[:10]):
    print(f"  {key}: {translations_to_update[key][:60]}")






