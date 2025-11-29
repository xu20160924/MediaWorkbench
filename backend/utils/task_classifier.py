"""
Task Type Classifier for Advertisement Tasks
Use this in your crawler to automatically classify tasks
"""


def classify_task_type(task_title: str) -> str:
    """
    Classify advertisement task type based on title keywords
    
    Keywords for community_special:
    - 社群
    - 社群特别征集
    - 社群专属任务  
    - 社群活动
    - 社群征集活动
    
    Args:
        task_title: The title of the advertisement task
        
    Returns:
        'community_special' if title contains any community keywords
        'normal' otherwise
    """
    # Keywords that indicate community special tasks
    community_keywords = [
        '社群',
        '社群特别征集',
        '社群专属任务',
        '社群活动',
        '社群征集活动'
    ]
    
    # Check if any keyword is in the title
    for keyword in community_keywords:
        if keyword in task_title:
            return 'community_special'
    
    return 'normal'


def get_task_type_label(task_type: str, lang: str = 'zh') -> str:
    """
    Get human-readable label for task type
    
    Args:
        task_type: 'community_special' or 'normal'
        lang: Language code ('zh' or 'en')
        
    Returns:
        Human-readable label
    """
    labels = {
        'zh': {
            'community_special': '社群特别任务',
            'normal': '普通任务'
        },
        'en': {
            'community_special': 'Community Special',
            'normal': 'Normal'
        }
    }
    
    return labels.get(lang, labels['zh']).get(task_type, task_type)
