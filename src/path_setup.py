"""
通用路径设置模块
用于统一处理Python路径设置，避免在多个文件中重复相同的代码
"""

import sys
import os


def setup_project_path():
    """
    设置项目路径，确保可以正确导入src模块
    
    这个函数会自动检测当前文件的位置，并将项目根目录添加到Python路径中
    支持从不同层级的文件调用（如src/、src/pages/、tests/等）
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 从src目录调用时，需要添加父目录（项目根目录）
    if current_dir.endswith('src'):
        project_root = os.path.dirname(current_dir)
    # 从src的子目录调用时，需要添加祖父目录（项目根目录）
    elif os.path.basename(os.path.dirname(current_dir)) == 'src':
        project_root = os.path.dirname(os.path.dirname(current_dir))
    # 从项目根目录调用时，添加当前目录
    else:
        project_root = current_dir
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    return project_root


def setup_src_path():
    """
    设置src路径，确保可以正确导入src模块
    
    这个函数专门用于页面文件，将src目录添加到Python路径中
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 从pages目录调用时，src目录是父目录
    if current_dir.endswith('pages'):
        src_dir = os.path.dirname(current_dir)
    # 从src目录调用时，src目录就是当前目录
    elif current_dir.endswith('src'):
        src_dir = current_dir
    # 从其他位置调用时，尝试找到src目录
    else:
        # 向上查找src目录
        search_dir = current_dir
        src_dir = None
        for _ in range(3):  # 最多向上查找3级
            potential_src = os.path.join(search_dir, 'src')
            if os.path.exists(potential_src) and os.path.isdir(potential_src):
                src_dir = potential_src
                break
            search_dir = os.path.dirname(search_dir)
        
        if src_dir is None:
            raise ImportError("无法找到src目录，请检查项目结构")
    
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    return src_dir


# 为了向后兼容，提供一个通用的设置函数
def setup_path():
    """
    通用路径设置函数，自动选择合适的路径设置方式
    """
    try:
        return setup_project_path()
    except Exception:
        return setup_src_path()