#!/usr/bin/env python3
"""
카테고리 수동 번역 스크립트

영어 이름을 기준으로 스페인어, 중국어, 일본어 번역을 직접 DB에 업데이트합니다.
"""

import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import TagCategory

# 영어 → 스페인어/중국어/일본어 번역 매핑
TRANSLATIONS = {
    # Level 1 카테고리
    1: {  # Hobbies · Lifestyle
        'es': 'Aficiones · Estilo de vida',
        'zh': '爱好 · 生活方式',
        'ja': '趣味 · ライフスタイル'
    },
    2: {  # Entertainment · Culture
        'es': 'Entretenimiento · Cultura',
        'zh': '娱乐 · 文化',
        'ja': 'エンターテインメント · 文化'
    },
    3: {  # Self-Development · Career
        'es': 'Desarrollo personal · Carrera',
        'zh': '自我发展 · 职业',
        'ja': '自己啓発 · キャリア'
    },
    4: {  # IT Technology
        'es': 'Tecnología IT',
        'zh': 'IT技术',
        'ja': 'IT技術'
    },
    # Level 2 카테고리 - 취미 · 라이프스타일 하위
    5: {  # Cooking · Baking
        'es': 'Cocina · Repostería',
        'zh': '烹饪 · 烘焙',
        'ja': '料理 · ベーキング'
    },
    6: {  # Travel · Camping
        'es': 'Viajes · Camping',
        'zh': '旅行 · 露营',
        'ja': '旅行 · キャンプ'
    },
    7: {  # Pets · Pet Care
        'es': 'Mascotas · Cuidado de mascotas',
        'zh': '宠物 · 宠物护理',
        'ja': 'ペット · ペットケア'
    },
    8: {  # Gardening · Plant Interior
        'es': 'Jardinería · Plantas de interior',
        'zh': '园艺 · 室内植物',
        'ja': 'ガーデニング · 観葉植物'
    },
    9: {  # Home Interior · DIY
        'es': 'Interior del hogar · Bricolaje',
        'zh': '家居装饰 · DIY',
        'ja': 'インテリア · DIY'
    },
    10: {  # Fashion · Beauty · Styling
        'es': 'Moda · Belleza · Estilismo',
        'zh': '时尚 · 美容 · 造型',
        'ja': 'ファッション · 美容 · スタイリング'
    },
    11: {  # Health · Exercise · Fitness
        'es': 'Salud · Ejercicio · Fitness',
        'zh': '健康 · 运动 · 健身',
        'ja': '健康 · 運動 · フィットネス'
    },
    12: {  # Music · Instruments
        'es': 'Música · Instrumentos',
        'zh': '音乐 · 乐器',
        'ja': '音楽 · 楽器'
    },
    # Level 2 카테고리 - 엔터테인먼트 · 문화 하위
    13: {  # Drama Analysis · Interpretation
        'es': 'Análisis de dramas · Interpretación',
        'zh': '戏剧分析 · 解读',
        'ja': 'ドラマ分析 · 解釈'
    },
    14: {  # Movie Review · Film Production Basics
        'es': 'Reseñas de películas · Fundamentos de producción cinematográfica',
        'zh': '电影评论 · 电影制作基础',
        'ja': '映画レビュー · 映画制作基礎'
    },
    15: {  # Variety Shows · Broadcast Content Analysis
        'es': 'Programas de variedades · Análisis de contenido de transmisión',
        'zh': '综艺节目 · 广播内容分析',
        'ja': 'バラエティ番組 · 放送コンテンツ分析'
    },
    16: {  # Music Appreciation · Music Video Interpretation
        'es': 'Apreciación musical · Interpretación de videos musicales',
        'zh': '音乐欣赏 · MV解读',
        'ja': '音楽鑑賞 · MV解釈'
    },
    17: {  # K-Pop · Idol Related Content
        'es': 'K-Pop · Contenido relacionado con ídolos',
        'zh': 'K-Pop · 偶像相关内容',
        'ja': 'K-Pop · アイドル関連コンテンツ'
    },
    18: {  # Culture · Trend Stories
        'es': 'Cultura · Historias de tendencias',
        'zh': '文化 · 趋势故事',
        'ja': '文化 · トレンドストーリー'
    },
    19: {  # OTT Recommendations · Content Guide
        'es': 'Recomendaciones OTT · Guía de contenido',
        'zh': 'OTT推荐 · 内容指南',
        'ja': 'OTTおすすめ · コンテンツガイド'
    },
    # Level 2 카테고리 - 자기계발 · 커리어 하위
    20: {  # Communication · Presentation
        'es': 'Comunicación · Presentación',
        'zh': '沟通 · 演讲',
        'ja': 'コミュニケーション · プレゼンテーション'
    },
    21: {  # Time Management · Productivity
        'es': 'Gestión del tiempo · Productividad',
        'zh': '时间管理 · 生产力',
        'ja': '時間管理 · 生産性'
    },
    22: {  # Office Work (Excel/Notion/PowerPoint)
        'es': 'Trabajo de oficina (Excel/Notion/PowerPoint)',
        'zh': '办公实务 (Excel/Notion/PowerPoint)',
        'ja': 'オフィス業務 (Excel/Notion/PowerPoint)'
    },
    23: {  # Leadership · Organization Management
        'es': 'Liderazgo · Gestión organizacional',
        'zh': '领导力 · 组织管理',
        'ja': 'リーダーシップ · 組織管理'
    },
    24: {  # Job Search · Career Change · Interview
        'es': 'Búsqueda de empleo · Cambio de carrera · Entrevista',
        'zh': '求职 · 转职 · 面试',
        'ja': '就職活動 · キャリアチェンジ · 面接'
    },
    25: {  # Economics · Investment · Real Estate
        'es': 'Economía · Inversión · Bienes raíces',
        'zh': '经济 · 投资 · 房地产',
        'ja': '経済 · 投資 · 不動産'
    },
    26: {  # Startup · Side Project
        'es': 'Startup · Proyecto secundario',
        'zh': '创业 · 副业项目',
        'ja': 'スタートアップ · 副業プロジェクト'
    },
    # Level 2 카테고리 - IT 기술 하위
    27: {  # Smartphone Usage
        'es': 'Uso de smartphones',
        'zh': '智能手机使用',
        'ja': 'スマートフォン使用'
    },
    28: {  # Excel · Data Basics
        'es': 'Excel · Fundamentos de datos',
        'zh': 'Excel · 数据基础',
        'ja': 'Excel · データ基礎'
    },
    29: {  # IT Technology
        'es': 'Tecnología IT',
        'zh': 'IT技术',
        'ja': 'IT技術'
    },
}


def update_category_translations():
    """카테고리 번역 업데이트"""
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    print("=== 카테고리 수동 번역 시작 ===\n")
    
    for category_id, translations in TRANSLATIONS.items():
        try:
            category = TagCategory.objects.get(id=category_id)
            
            # 스페인어 번역
            if 'es' in translations:
                category.name_es = translations['es']
                category.is_es_complete = True
            
            # 중국어 번역
            if 'zh' in translations:
                category.name_zh = translations['zh']
                category.is_zh_complete = True
            
            # 일본어 번역
            if 'ja' in translations:
                category.name_ja = translations['ja']
                category.is_ja_complete = True
            
            # 저장
            update_fields = ['name_es', 'name_zh', 'is_es_complete', 'is_zh_complete']
            if 'ja' in translations:
                update_fields.extend(['name_ja', 'is_ja_complete'])
            category.save(update_fields=update_fields)
            
            updated_count += 1
            lang_list = []
            if 'es' in translations:
                lang_list.append('es')
            if 'zh' in translations:
                lang_list.append('zh')
            if 'ja' in translations:
                lang_list.append('ja')
            print(f"✓ [{category.id}] {category.name_en}: {', '.join(lang_list)} 번역 완료")
            
        except TagCategory.DoesNotExist:
            error_count += 1
            print(f"✗ [{category_id}]: 카테고리를 찾을 수 없습니다")
        except Exception as e:
            error_count += 1
            print(f"✗ [{category_id}]: 오류 발생 - {str(e)}")
    
    print(f"\n=== 번역 완료 ===")
    print(f"총 처리: {len(TRANSLATIONS)}개")
    print(f"번역 완료: {updated_count}개")
    print(f"오류: {error_count}개")


if __name__ == '__main__':
    update_category_translations()



