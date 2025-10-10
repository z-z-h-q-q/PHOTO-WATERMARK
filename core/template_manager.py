"""
水印模板管理模块，负责存储和管理水印模板。
依赖：json
"""
import json
import os

class TemplateManager:
    def __init__(self, template_file="templates.json"):
        self.template_file = template_file
        self.templates = self._load_templates()

    def _load_templates(self):
        """从文件加载模板"""
        if not os.path.exists(self.template_file):
            return {}
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载模板失败: {e}")
            return {}

    def save_template(self, name, properties):
        """保存水印模板"""
        self.templates[name] = properties
        try:
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False

    def get_template(self, name):
        """获取指定模板"""
        return self.templates.get(name)

    def list_templates(self):
        """列出所有模板"""
        return list(self.templates.keys())

    def delete_template(self, name):
        """删除模板"""
        if name in self.templates:
            del self.templates[name]
            try:
                with open(self.template_file, 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"删除模板失败: {e}")
        return False